import typer
import asyncio
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from loguru import logger

from src.services.coingecko import CoinGeckoService
from src.services.web_search import WebSearchService
from src.core.llm_engine import LLMEngine
from src.core.rag_engine import RAGEngine
from src.core.risk_engine import RiskEngine
from src.utils.report_gen import ReportGenerator
from config.settings import settings

app = typer.Typer()
console = Console()

cg_service = CoinGeckoService()
web_search = WebSearchService()
llm = LLMEngine()
rag = RAGEngine()
risk_engine = RiskEngine()

@app.command()
def dashboard():
    """📈 Gyorsított Piaci Műszerfal aszinkron párhuzamosítással."""
    console.clear()
    console.rule(f"[bold blue]{settings.APP_NAME} - MARKET DASHBOARD[/bold blue]")

    async def fetch_coin(coin: str, sem: asyncio.Semaphore, progress: Progress, task_id):
        async with sem:
            # 1 másodperc késleltetés a CoinGecko limit miatt, de a Semaphore miatt ez szabályozott
            await asyncio.sleep(1.0) 
            data = await cg_service.get_coin_data(coin)
            progress.update(task_id, advance=1)
            if data:
                metrics = risk_engine.calculate_risk_metrics(data)
                data['risk_score'] = metrics['quantitative_score']
            return data

    async def show_market():
        target_coins = ["bitcoin", "ethereum", "solana", "ripple", "pepe", "cardano"]
        
        # Párhuzamosítás korlátozása: egyszerre max 2 kérés menjen a CoinGecko felé
        semaphore = asyncio.Semaphore(2)
        
        with Progress(SpinnerColumn(), TextColumn("[cyan]Adatok letöltése párhuzamosan..."), transient=True) as progress:
            task = progress.add_task("", total=len(target_coins))
            
            # PÁRHUZAMOS FUTTATÁS
            tasks = [fetch_coin(coin, semaphore, progress, task) for coin in target_coins]
            results = await asyncio.gather(*tasks)

        market_data = [res for res in results if res is not None]

        table = Table(title="🔥 LIVE MARKET DATA 🔥", border_style="green")
        table.add_column("Rank", justify="center"); table.add_column("Name", style="magenta")
        table.add_column("Price (USD)", justify="right"); table.add_column("24h Change", justify="right")
        table.add_column("Math Risk Score", justify="center")

        for coin in market_data:
            price = coin.get('market_data', {}).get('current_price', {}).get('usd', 0)
            change = coin.get('market_data', {}).get('price_change_percentage_24h', 0)
            score = coin.get('risk_score', 50)
            
            c_style = "green" if change > 0 else "red"
            r_style = "green" if score < 40 else ("yellow" if score < 70 else "red")
            
            table.add_row(str(coin.get('market_cap_rank', 'N/A')), coin.get('name'), 
                          f"${price:,.2f}", f"[{c_style}]{change:.2f}%[/{c_style}]", 
                          f"[{r_style}]{score:.0f}/100[/{r_style}]")
        console.print(table)

    asyncio.run(show_market())

@app.command()
def audit(token: str):
    """🛡️ Deep Audit párhuzamos lekérdezésekkel."""
    async def run_audit():
        console.rule(f"[bold red]DEEP AUDIT: {token.upper()}[/bold red]")
        
        with Progress(SpinnerColumn(), TextColumn("{task.description}"), transient=True) as progress:
            progress.add_task("[cyan]Adatok letöltése...", total=None)
            data = await cg_service.get_coin_data(token)
            if not data:
                console.print("[red]❌ Token nem található![/red]"); return

            progress.add_task("[blue]Párhuzamos feladatok (RAG & Web Search) futtatása...", total=None)
            
            # RAG és Hírek keresése EGYSZERRE (Párhuzamosan)
            rag_task = asyncio.to_thread(rag.load_context)
            news_task = web_search.search_news(data['name'])
            
            context, latest_news = await asyncio.gather(rag_task, news_task)
            
            math_score = risk_engine.calculate_risk_metrics(data)['quantitative_score']

            progress.add_task(f"[magenta]AI Elemzés ({settings.MODEL_NAME})...", total=None)
            
            user_prompt = (
                f"PROJECT: {data['name']}\nMATH RISK: {math_score}/100\n"
                f"NEWS: {latest_news}\nRULES: {context}\n"
                "REQUIRED JSON: {'verdict': 'Safe/Scam/High Risk', 'score': 0-100, 'summary': 'text', 'pros': [], 'cons': []}"
            )
            
            # ASYNC AI HÍVÁS
            analysis = await llm.analyze_json(user_prompt, "You are a Crypto Auditor. Output JSON.")

        if not analysis or "error" in analysis:
            console.print("[red]Hiba az AI elemzésben.[/red]")
        else:
            verdict = analysis.get('verdict', 'Unknown')
            color = "green" if verdict == "Safe" else "red"
            console.print(Panel(f"[bold]Verdict: [{color}]{verdict}[/{color}][/bold]\nScore: {analysis.get('score')}/100", border_style=color))
            
            path = ReportGenerator.create_pdf(analysis, token)
            if path: console.print(f"[green]✅ PDF: {path}[/green]")

    asyncio.run(run_audit())

if __name__ == "__main__":
    app()