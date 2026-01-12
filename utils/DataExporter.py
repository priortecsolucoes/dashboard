import time
from datetime import datetime, date, timedelta
import calendar
import requests
import io
import pandas as pd
from collections import Counter
from dotenv import load_dotenv
import os

class DataExporter:
    def __init__(self):
        load_dotenv()
        self.motivations = {
            "atendimento recorrente",
            "atendimento sos",
            "atendimento pontual", 
            "alta",
            "emergência do cliente",
            "atendimento interrompido pelo cliente",
            "questão pessoal ou emergência do cliente"
        }
        self.pendingAuthorizationInArrearsCurrentMonth = []
        self.billableNotAuthorized = []
        self.authorizedBillable = []
        self.deniedRecords = []
        self.ineligibleRecords = []
        self.headers = {
            "Authorization": f"Basic {os.getenv('IMND_ACCESS_TOKEN')}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def requestWithRetries(self, url, maxRetries=2):
        attempt = 0
        while attempt <= maxRetries:
            try:
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                print(f"⚠️ Erro na requisição ({attempt + 1}/{maxRetries}): {e}")
            attempt += 1
            time.sleep(5)
        print("❌ Falha ao obter dados da API.")
        return None

    def loadData(self):
        print(f"Iniciando tarefa às {datetime.now()}")
        try:
            firstDayOfMonth = date.today().replace(day=1)
            lastDay = calendar.monthrange(date.today().year, date.today().month)[1]
            lastDayOfMonth = date.today().replace(day=lastDay)
            dateStart = firstDayOfMonth.strftime("%Y-%m-%d")
            dateEnd = lastDayOfMonth.strftime("%Y-%m-%d")

            page = 1
            hasMore = True
            self.allNodes = []

            while hasMore:
                apiUrl = (f"https://imnd.com.br/api/automation/appointments?page={page}&"
                          f"status=scheduled,fulfilled,notaccomplished,rescheduled,inprogress,rescheduled_24,notaccomplished_24&limit=1000&"
                          f"date_start={dateStart}&date_end={dateEnd}")

                print(f"🔄 Requisitando página {page}...")
                requisicao = self.requestWithRetries(apiUrl)
                if requisicao is None:
                    break
                try:
                    data = requisicao.json()
                    self.allNodes.extend(data.get("nodes", []))
                    hasMore = data.get("metadata", {}).get("pagination", {}).get("has_more", False)
                    page += 1
                except Exception as e:
                    print(f"❌ Erro ao processar JSON: {e}")
                    break
                time.sleep(5)
            return self.allNodes
        except Exception as erro:
            print("Erro ao carregar dados", erro)

    def exportToExcel(self, data, filename):
        if not data:
            import streamlit as st
            st.warning("❌ Nenhum dado para exportar.")
            return None, None

        df = pd.DataFrame(data)

        if 'metas' in df.columns:
            df.drop(columns=['metas'], inplace=True)

        # Cria um buffer em memória
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Dados')
        output.seek(0)

        return output, filename

    def checkPendingAuthorizationForCurrentMonth(self):
        nodes = self.loadData()
        today = date.today()
        
        for node in nodes:
            try:
                nodeDateTimeStr = node.get("data", "01/01/1970")
                nodeDateTime = datetime.strptime(nodeDateTimeStr, "%d/%m/%Y").date()
                nodeMotivation = (node.get("motivacao") or "").lower().strip()
                nodeStatus = node.get("metas", {}).get("ts_status")

                if (nodeDateTime <= today) and \
                   nodeMotivation in self.motivations and \
                   (nodeStatus is None or nodeStatus == ""):
                    self.pendingAuthorizationInArrearsCurrentMonth.append(node)
            except ValueError as erro:
                print(f"❌ Erro ao converter data '{node.get('data', 'Desconhecida')}': {erro}")

        filename = f"Registros_Autorizacoes_Pendentes_Atrasadas_{datetime.now().strftime('%Y%m%d')}.xlsx"
        return self.exportToExcel(self.pendingAuthorizationInArrearsCurrentMonth, filename)

    def processNotBillableQueries(self):
        nodes = self.loadData()
        today = date.today()
        
        for node in nodes:
            try:
                nodeDateTimeStr = node.get("data", "01/01/1970")
                nodeDateTime = datetime.strptime(nodeDateTimeStr, "%d/%m/%Y").date()
                nodeMotivation = (node.get("motivacao") or "").lower().strip()
                nodeStatus = node.get("metas", {}).get("ts_status")

                if nodeDateTime <= today and nodeMotivation in self.motivations and (nodeStatus is None or nodeStatus == ""):
                    self.billableNotAuthorized.append(node)
            except ValueError as erro:
                print(f"❌ Erro ao converter data '{node.get('data', 'Desconhecida')}': {erro}")

        filename = f"Registros_Nao_Faturaveis_{datetime.now().strftime('%Y%m%d')}.xlsx"
        return self.exportToExcel(self.billableNotAuthorized, filename)

    def processBillableQueries(self):
        nodes = self.loadData()
        today = date.today()
        
        for node in nodes:
            try:
                nodeDateTimeStr = node.get("data", "01/01/1970")
                nodeDateTime = datetime.strptime(nodeDateTimeStr, "%d/%m/%Y").date()
                nodeMotivation = (node.get("motivacao") or "").lower().strip()
                nodeStatus = (node.get("metas", {}).get("ts_status") or "").lower().strip()

                if nodeDateTime <= today and nodeMotivation in self.motivations and nodeStatus == "aprovado":
                    self.authorizedBillable.append(node)
            except ValueError as erro:
                print(f"❌ Erro ao converter data '{node.get('data', 'Desconhecida')}': {erro}")

        filename = f"Registros_Faturaveis_Autorizados_{datetime.now().strftime('%Y%m%d')}.xlsx"
        return self.exportToExcel(self.authorizedBillable, filename)


    def processDeniedQueries(self):
        nodes = self.loadData()
        today = date.today()

        for node in nodes:
            try:
                nodeDateTimeStr = node.get("data", "01/01/1970")
                nodeDateTime = datetime.strptime(nodeDateTimeStr, "%d/%m/%Y").date()
                nodeStatus = (node.get("metas", {}).get("ts_status") or "").lower().strip()
                nodeMotivation = (node.get("motivacao") or "").lower().strip()

                if nodeDateTime <= today and nodeMotivation in self.motivations and nodeStatus == "negado":
                    self.deniedRecords.append(node)
            except ValueError as erro:
                print(f"\u274C Erro ao converter data '{node.get('data', 'Desconhecida')}': {erro}")

        filename = f"Registros_Negados_{datetime.now().strftime('%Y%m%d')}.xlsx"
        return self.exportToExcel(self.deniedRecords, filename)

    def processIneligibleQueries(self):
        nodes = self.loadData()
        today = date.today()

        for node in nodes:
            try:
                nodeDateTimeStr = node.get("data", "01/01/1970")
                nodeDateTime = datetime.strptime(nodeDateTimeStr, "%d/%m/%Y").date()
                nodeStatus = (node.get("metas", {}).get("ts_status") or "").lower().strip()
                nodeMotivation = (node.get("motivacao") or "").lower().strip()

                if nodeDateTime <= today and nodeMotivation in self.motivations and nodeStatus == "inelegível":
                    self.ineligibleRecords.append(node)
            except ValueError as erro:
                print(f"\u274C Erro ao converter data '{node.get('data', 'Desconhecida')}': {erro}")

        filename = f"Registros_Inelegiveis_{datetime.now().strftime('%Y%m%d')}.xlsx"
        return self.exportToExcel(self.ineligibleRecords, filename)
