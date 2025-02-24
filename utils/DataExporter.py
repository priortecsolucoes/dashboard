import time
from datetime import datetime, date, timedelta
import calendar
import requests
import pandas as pd
from collections import Counter
from dotenv import load_dotenv
class DataExporter:
    def __init__(self):
        load_dotenv()
        self.motivations = {
            "atendimento recorrente",
            "atendimento sos",
            "atendimento pontual", 
            "alta",
            "emergência do cliente",
            "atendimento interrompido pelo cliente"
        }
        self.pendingAuthorizationInArrearsCurrentMonth = []
        self.billableNotAuthorized = []
        self.authorizedBillable = []
        self.headers = os.getenv("IMND_ACCESS_TOKEN")

    def requestWithRetries(self, url, maxRetries=2):
        attempt = 0
        while attempt <= maxRetries:
            try:
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                print(f"⚠️ Erro na requisição ({attempt + 1}/{maxRetries}): {e}")
                if attempt == maxRetries:
                    print("🚨 Tentativas esgotadas. Verifique sua conexão ou a API.")
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
                          f"status=scheduled,fulfilled,notaccomplished&limit=1000&"
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

            aprovados = [node for node in self.allNodes if node.get("metas", {}).get("ts_status") == "APROVADO"]
            return self.allNodes
        except Exception as erro:
            print("Erro ao carregar dados", erro)

    def checkPendingAuthorizationForCurrentMonth(self):
        today = date.today()
        limitDate = today - timedelta(days=3)
        for node in self.allNodes:
            try:
                nodeDateTimeStr = node.get("data", "01/01/1970")
                nodeDateTime = datetime.strptime(nodeDateTimeStr, "%d/%m/%Y").date()
                nodeMotivation = (node.get("motivacao") or "").lower().strip()
                nodeStatus = node.get("metas", {}).get("ts_status")

                if (limitDate <= nodeDateTime <= today) and \
                   nodeMotivation in self.motivations and \
                   (nodeStatus is None or nodeStatus == ""):
                    print(f"🟠 Consulta autorização pendente atrasada: {node['data']}")
                    self.pendingAuthorizationInArrearsCurrentMonth.append(node)
            except ValueError as erro:
                print(f"❌ Erro ao converter data '{node.get('data', 'Desconhecida')}': {erro}")
        self.exportToExcel()

    def processNotBillableQueries(self):
        today = date.today()
        limitDate = today - timedelta(days=3)
        startOfMonth = today.replace(day=1)

        for node in self.allNodes:
            try:
                nodeDateTimeStr = node.get("data", "01/01/1970")
                nodeDateTime = datetime.strptime(nodeDateTimeStr, "%d/%m/%Y").date()
                nodeMotivation = (node.get("motivacao") or "").lower().strip()
                nodeStatus = node.get("metas", {}).get("ts_status")

                if startOfMonth <= nodeDateTime < limitDate and nodeMotivation in self.motivations and (nodeStatus is None or nodeStatus == ""):
                    print(f"⚠️ Consulta faturável NÃO autorizada encontrada: {node['data']}")
                    self.billableNotAuthorized.append(node)
            except ValueError as erro:
                print(f"❌ Erro ao converter data '{node.get('data', 'Desconhecida')}': {erro}")

        print(f"🔍 Total de registros faturáveis NÃO autorizados: {len(self.billableNotAuthorized)}")
        self.exportNotBillableToExcel()

    def processBillableQueries(self):
        today = date.today()
        limitDate = today - timedelta(days=3)

        for node in self.allNodes:
            try:
                nodeDateTimeStr = node.get("data", "01/01/1970")
                nodeDateTime = datetime.strptime(nodeDateTimeStr, "%d/%m/%Y").date()
                nodeMotivation = (node.get("motivacao") or "").lower().strip()
                nodeStatus = (node.get("metas", {}).get("ts_status") or "").lower().strip()

                if nodeDateTime <= limitDate and nodeMotivation in self.motivations and nodeStatus == "aprovado":
                    print(f"✅ Consulta faturável AUTORIZADA encontrada: {node['data']}")
                    self.authorizedBillable.append(node)
            except ValueError as erro:
                print(f"❌ Erro ao converter data '{node.get('data', 'Desconhecida')}': {erro}")

        print(f"🔍 Total de registros faturáveis AUTORIZADOS: {len(self.authorizedBillable)}")
        self.exportBillableToExcel()

    def exportToExcel(self):
        if not self.pendingAuthorizationInArrearsCurrentMonth:
            print("❌ Nenhum dado para exportar.")
            return
        df = pd.DataFrame(self.pendingAuthorizationInArrearsCurrentMonth)
        if 'metas' in df.columns:
            df.drop(columns=['metas'], inplace=True)
        df.loc[:, 'label'] = df['data']  # Exemplo para evitar view/copy warning

        fileName = f"Registros_Autorizacoes_Pendentes_Atrasadas_{datetime.now().strftime('%Y%m%d')}.xlsx"
        df.to_excel(fileName, index=False)
        print(f"📂 Planilha gerada com sucesso: {fileName}")

    def exportNotBillableToExcel(self):
        if not self.billableNotAuthorized:
            print("❌ Nenhum dado faturável NÃO autorizado para exportar.")
            return
        df = pd.DataFrame(self.billableNotAuthorized)
        if 'metas' in df.columns:
            df.drop(columns=['metas'], inplace=True)
        df.loc[:, 'label'] = df['data']

        fileName = f"Registros_Nao_Faturaveis_{datetime.now().strftime('%Y%m%d')}.xlsx"
        df.to_excel(fileName, index=False)
        print(f"📂 Planilha de registros NÃO faturáveis gerada com sucesso: {fileName}")

    def exportBillableToExcel(self):
        if not self.authorizedBillable:
            print("❌ Nenhum dado faturável autorizado para exportar.")
            return
        df = pd.DataFrame(self.authorizedBillable)
        if 'metas' in df.columns:
            df.drop(columns=['metas'], inplace=True)
        df.loc[:, 'label'] = df['data']

        fileName = f"Registros_Faturaveis_Autorizados_{datetime.now().strftime('%Y%m%d')}.xlsx"
        df.to_excel(fileName, index=False)
        print(f"📂 Planilha de registros faturáveis AUTORIZADOS gerada com sucesso: {fileName}")

    def run(self):
        self.loadData()
        self.checkPendingAuthorizationForCurrentMonth()
        self.processNotBillableQueries()
        self.processBillableQueries()

if __name__ == "__main__":
    exporter = DataExporter()
    exporter.run()

