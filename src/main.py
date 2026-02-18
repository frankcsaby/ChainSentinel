import typer
import asyncio
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from loguru import logger

# Saját modulok
from src.services.coingecko import CoinGeckoService
from src.services.news import NewsService  # <--- ÚJ IMPORT
from src.core.llm_engine import LLMEngine
from src.core.rag_engine import RAGEngine
from src.utils.report_gen import ReportGenerator
from config.settings import settings

app = typer.Typer()
console = Console()

# Szolgáltatások
cg_service = CoinGeckoService()
news_service = NewsService()  # <--- ÚJ PÉLDÁNY
llm = LLMEngine()
rag = RAGEngine()

@app.command()
def dashboard():
    """
    📈 Élő Piaci Műszerfal (Rate Limit védelemmel).
    """
    console.clear()
    console.rule(f"[bold blue]{settings.APP_NAME} - MARKET DASHBOARD[/bold blue]")

    async def show_market():
        target_coins = ["bitcoin", "ethereum", "solana", "pepe", "ripple"]
        market_data = []

        with Progress(SpinnerColumn(), TextColumn("[cyan]Piaci adatok letöltése..."), transient=True) as progress:
            task = progress.add_task("", total=len(target_coins))
            for coin in target_coins:
                data = await cg_service.get_coin_data(coin)
                if data: market_data.append(data)
                progress.update(task, advance=1)
                await asyncio.sleep(1.2) # Rate Limit védelem

        table = Table(title="🔥 LIVE MARKET DATA 🔥", border_style="green")
        table.add_column("Rank", justify="center", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Price", justify="right", style="green")
        table.add_column("24h Change", justify="right")
        
        for coin in market_data:
            price = coin['market_data']['current_price']['usd']
            change = coin['market_data']['price_change_percentage_24h']
            rank = coin['market_cap_rank']
            change_style = "green" if change > 0 else "red"
            
            table.add_row(str(rank), coin['name'], f"${price:,.2f}", f"[{change_style}]{change:.2f}%[/{change_style}]")

        console.print(table)

    asyncio.run(show_market())

@app.command()
def audit(token: str):
    """
    🛡️ Deep Audit: RAG + AI + WEB SEARCH (Hírek).
    """
    async def run_audit():
        console.rule(f"[bold red]DEEP AUDIT: {token.upper()}[/bold red]")
        
        with Progress(SpinnerColumn(), TextColumn("{task.description}"), transient=True) as progress:
            # 1. Adatgyűjtés
            progress.add_task("[cyan]Adatok letöltése...", total=None)
            data = await cg_service.get_coin_data(token)
            if not data:
                console.print(f"[red]❌ Token nem található: {token}[/red]")
                return

            # 2. Tudásbázis (RAG)
            progress.add_task("[yellow]Tudásbázis betöltése...", total=None)
            context = rag.load_context()

            # 3. Hírek keresése (ÚJ FUNKCIÓ)
            progress.add_task("[blue]Friss hírek keresése a weben...", total=None)
            latest_news = news_service.get_latest_news(data['name'])

            # 4. AI Elemzés
            progress.add_task(f"[magenta]AI Elemzés ({settings.MODEL_NAME})...", total=None)
            
            desc = data.get('description', {}).get('en', '')[:1000]
            stats = f"Price: ${data['market_data']['current_price']['usd']}, ATH Change: {data['market_data']['ath_change_percentage']['usd']}%"

            system_prompt = "You are a Senior Crypto Risk Auditor. Detect SCAMS based on data, news, and rules. Output JSON."
            
            # A Promptba most már belefűzzük a HÍREKET is!
            user_prompt = (
                f"PROJECT: {data['name']}\nSTATS: {stats}\nDESC: {desc}\n\n"
                f"LATEST NEWS (Check for hacks/scams): {latest_news}\n\n"
                f"KNOWLEDGE BASE RULES: {context}\n\n"
                "REQUIRED JSON: {'verdict': 'Safe/Scam/High Risk', 'score': 0-100, 'summary': 'text', 'pros': [], 'cons': []}"
            )
            
            analysis = llm.analyze_json(user_prompt, system_prompt)

        # 5. Eredmény
        if not analysis or "error" in analysis:
            console.print("[red]Hiba az elemzésben.[/red]")
        else:
            color = "green" if analysis['verdict'] == "Safe" else "red"
            console.print(Panel(
                f"[bold]Verdict: [{color}]{analysis['verdict']}[/{color}][/bold]\nScore: {analysis['score']}/100\n\n[italic]{analysis['summary']}[/italic]\n\n[bold]Latest News Checked:[/bold]\n{latest_news[:200]}...",
                title=f"AUDIT: {token.upper()}", border_style=color
            ))
            
            path = ReportGenerator.create_pdf(analysis, token)
            if path: console.print(f"[green]✅ PDF: {path}[/green]")

    asyncio.run(run_audit())

if __name__ == "__main__":
    app()