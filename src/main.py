import typer
import asyncio
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from loguru import logger

# --- SAJÁT MODULOK IMPORTÁLÁSA ---
# Győződj meg róla, hogy ezek a fájlok léteznek a megfelelő mappákban!
from src.services.coingecko import CoinGeckoService
from src.services.web_search import WebSearchService  # <--- Az új kereső modul
from src.core.llm_engine import LLMEngine
from src.core.rag_engine import RAGEngine
from src.core.risk_engine import RiskEngine          # <--- Az új matekos modul
from src.utils.report_gen import ReportGenerator
from config.settings import settings

# --- INICIALIZÁLÁS ---
app = typer.Typer()
console = Console()

# Szolgáltatások példányosítása
cg_service = CoinGeckoService()
web_search = WebSearchService()
llm = LLMEngine()
rag = RAGEngine()
risk_engine = RiskEngine()

@app.command()
def dashboard():
    """
    📈 Élő Piaci Műszerfal (Dashboard)
    Védett mód: Lassított lekérdezés a Rate Limit elkerülése érdekében.
    """
    console.clear()
    console.rule(f"[bold blue]{settings.APP_NAME} - MARKET DASHBOARD[/bold blue]")

    async def show_market():
        # Ezeket a coinokat figyeljük a főoldalon
        target_coins = ["bitcoin", "ethereum", "solana", "ripple", "pepe", "cardano"]
        market_data = []

        with Progress(SpinnerColumn(), TextColumn("[cyan]Piaci adatok letöltése (kérlek várj)..."), transient=True) as progress:
            task = progress.add_task("", total=len(target_coins))
            
            for coin in target_coins:
                # 1. Adatletöltés
                data = await cg_service.get_coin_data(coin)
                
                if data:
                    # Kiszámoljuk a gyors kockázati pontszámot a táblázathoz
                    metrics = risk_engine.calculate_risk_metrics(data)
                    data['risk_score'] = metrics['quantitative_score']
                    market_data.append(data)
                
                progress.update(task, advance=1)
                
                # 2. Rate Limit védelem (fontos!)
                await asyncio.sleep(1.2) 

        # Táblázat felépítése
        table = Table(title="🔥 LIVE MARKET DATA & RISK ANALYSIS 🔥", border_style="green")
        table.add_column("Rank", justify="center", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Price (USD)", justify="right", style="green")
        table.add_column("24h Change", justify="right")
        table.add_column("Math Risk Score", justify="center") # Új oszlop!

        for coin in market_data:
            m_data = coin.get('market_data', {})
            price = m_data.get('current_price', {}).get('usd', 0)
            change = m_data.get('price_change_percentage_24h', 0)
            rank = coin.get('market_cap_rank', 'N/A')
            risk_score = coin.get('risk_score', 50)
            
            # Formázás és Színezés
            change_str = f"{change:.2f}%"
            change_style = "green" if change > 0 else "red"
            
            # Kockázat színezése (0-100)
            risk_style = "green" if risk_score < 40 else ("yellow" if risk_score < 70 else "red")

            table.add_row(
                str(rank),
                coin.get('name'),
                f"${price:,.2f}",
                f"[{change_style}]{change_str}[/{change_style}]",
                f"[{risk_style}]{risk_score:.0f}/100[/{risk_style}]"
            )

        console.print(table)
        console.print("\n[dim]Tipp: Részletes elemzéshez: python -m src.main audit [token_neve][/dim]")

    asyncio.run(show_market())

@app.command()
def audit(token: str):
    """
    🛡️ Deep Audit: 4 szintű elemzés (Adat + Matek + Hírek + RAG).
    """
    async def run_audit():
        console.rule(f"[bold red]DEEP AUDIT: {token.upper()}[/bold red]")
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
            
            # 1. API ADATOK
            progress.add_task("[cyan]1/4 Adatok letöltése CoinGecko-ról...", total=None)
            data = await cg_service.get_coin_data(token)
            
            if not data:
                console.print(f"[bold red]❌ A '{token}' token nem található, vagy API hiba történt![/bold red]")
                return

            # 2. TUDÁSBÁZIS (RAG)
            progress.add_task("[yellow]2/4 Tudásbázis (.txt) betöltése...", total=None)
            context = rag.load_context()

            # 3. KOCKÁZATI MOTOR (MATEK) & HÍREK (WEB)
            progress.add_task("[blue]3/4 Kvantitatív elemzés és Hírek keresése...", total=None)
            
            # Matek futtatása
            risk_metrics = risk_engine.calculate_risk_metrics(data)
            math_score = risk_metrics['quantitative_score']
            liquidity = risk_metrics['metrics'].get('liquidity_ratio', 0)
            
            # Hírek keresése
            latest_news = web_search.search_news(data['name'])

            # 4. AI AGY (LLM)
            progress.add_task(f"[magenta]4/4 AI Elemzés generálása ({settings.MODEL_NAME})...", total=None)
            
            # Prompt összerakása
            desc = data.get('description', {}).get('en', '')[:1000]
            stats = f"Price: ${data['market_data']['current_price']['usd']}, ATH Change: {data['market_data']['ath_change_percentage']['usd']}%"

            system_prompt = (
                "You are a Senior Crypto Risk Auditor. "
                "Your goal is to detect SCAMS based on quantitative data, news, and knowledge base rules. "
                "Output STRICT JSON only."
            )
            
            user_prompt = (
                f"PROJECT: {data['name']}\n"
                f"MATH RISK SCORE: {math_score}/100 (Calculated by algorithms)\n"
                f"LIQUIDITY RATIO: {liquidity}\n"
                f"STATS: {stats}\n"
                f"DESCRIPTION: {desc}\n\n"
                f"LATEST WEB NEWS: {latest_news}\n\n"
                f"KNOWLEDGE BASE RULES: {context}\n\n"
                "REQUIRED JSON OUTPUT:\n"
                "{\n"
                '  "verdict": "Safe" or "Scam" or "High Risk",\n'
                '  "score": (int 0-100, combine math score with your judgment),\n'
                '  "summary": "Executive summary (max 3 sentences)",\n'
                '  "pros": ["Strength 1", "Strength 2"],\n'
                '  "cons": ["Risk 1", "Risk 2"]\n'
                "}"
            )
            
            analysis = llm.analyze_json(user_prompt, system_prompt)

        # EREDMÉNY MEGJELENÍTÉSE
        if not analysis or "error" in analysis:
            console.print(f"[red]Hiba az AI elemzésben: {analysis.get('error', 'Unknown')}[/red]")
        else:
            verdict = analysis.get('verdict', 'Unknown')
            color = "green" if verdict == "Safe" else "red"
            
            # Panel a konzolra
            console.print(Panel(
                f"[bold]Verdict: [{color}]{verdict}[/{color}][/bold]\n"
                f"Final Risk Score: {analysis.get('score')}/100\n"
                f"(Algorithmic Base Score: {math_score}/100)\n\n"
                f"[italic]{analysis.get('summary')}[/italic]\n\n"
                f"[bold]Latest News Context:[/bold]\n{latest_news[:150]}...",
                title=f"AUDIT RESULT: {token.upper()}", border_style=color
            ))

            # PDF Generálás
            pdf_path = ReportGenerator.create_pdf(analysis, token)
            if pdf_path:
                console.print(f"\n[green]✅ PDF Jelentés elmentve: {pdf_path}[/green]")

    asyncio.run(run_audit())

@app.command()
def portfolio(budget: int = 10000, strategy: str = "balanced"):
    """
    💰 AI Portfólió Tanácsadó (Excel exporttal).
    Használat: python -m src.main portfolio --budget 5000 --strategy safe
    """
    async def run_portfolio():
        console.rule("[bold green]ROBO-ADVISOR AI[/bold green]")
        
        with Progress(SpinnerColumn(), TextColumn("[magenta]Portfólió stratégia generálása..."), transient=True) as progress:
            progress.add_task("", total=None)
            
            # Demó jelöltek
            candidates = "Bitcoin, Ethereum, Solana, USDC, Pepe, Cardano, Polkadot, Chainlink"
            
            system_prompt = "You are a Portfolio Manager. Output JSON only."
            user_prompt = (
                f"Create a portfolio allocation for ${budget} USD.\n"
                f"Strategy: {strategy} (Safe/Balanced/Risky).\n"
                f"Candidates available: {candidates}\n\n"
                "REQUIRED JSON OUTPUT STRUCTURE:\n"
                "{\n"
                '  "allocation": {"Asset Name": Amount_USD (int)},\n'
                '  "reasoning": "Why you chose this distribution"\n'
                "}"
            )
            
            plan = llm.analyze_json(user_prompt, system_prompt)

        if not plan or "error" in plan:
            console.print("[red]Hiba a generáláskor.[/red]")
        else:
            console.print(Panel(
                f"[bold]Stratégia:[/bold] {strategy.upper()}\n[bold]Indoklás:[/bold] {plan.get('reasoning')}",
                title="BEFEKTETÉSI TERV", border_style="blue"
            ))
            
            # Táblázat
            table = Table(title="Asset Allocation")
            table.add_column("Asset", style="cyan")
            table.add_column("Amount ($)", justify="right", style="green")
            table.add_column("Percentage", justify="right")
            
            allocs = plan.get('allocation', {})
            export_data = []
            
            for asset, amount in allocs.items():
                percent = (amount / budget) * 100
                table.add_row(asset, f"${amount:,.2f}", f"{percent:.1f}%")
                export_data.append({"Asset": asset, "Amount ($)": amount, "Percentage": f"{percent:.1f}%"})
                
            console.print(table)
            
            # Excel mentés
            excel_path = ReportGenerator.export_to_excel(export_data, f"Portfolio_{strategy}")
            if excel_path:
                console.print(f"\n[cyan]📊 Excel exportálva: {excel_path}[/cyan]")

    asyncio.run(run_portfolio())

if __name__ == "__main__":
    app()