import typer
import asyncio
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from loguru import logger

# --- SAJÁT MODULOK IMPORTÁLÁSA ---
from src.services.coingecko import CoinGeckoService
from src.services.web_search import WebSearchService
from src.core.llm_engine import LLMEngine
from src.core.rag_engine import RAGEngine
from src.core.risk_engine import RiskEngine
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
    📈 Élő Piaci Műszerfal aszinkron párhuzamosítással és Rate Limit védelemmel.
    """
    console.clear()
    console.rule(f"[bold blue]{settings.APP_NAME} - MARKET DASHBOARD[/bold blue]")

    async def fetch_coin(coin: str, sem: asyncio.Semaphore, progress: Progress, task_id):
        async with sem:
            # Rövid várakozás a 429-es CoinGecko hiba elkerülése miatt
            await asyncio.sleep(1.0)
            data = await cg_service.get_coin_data(coin)
            progress.update(task_id, advance=1)
            
            if data:
                metrics = risk_engine.calculate_risk_metrics(data)
                data['risk_score'] = metrics['quantitative_score']
            return data

    async def show_market():
        target_coins = ["bitcoin", "ethereum", "solana", "ripple", "pepe", "cardano"]
        
        # Párhuzamosítás korlátozása: egyszerre max 2 kérés menjen
        semaphore = asyncio.Semaphore(2)
        
        with Progress(SpinnerColumn(), TextColumn("[cyan]Piaci adatok letöltése párhuzamosan..."), transient=True) as progress:
            task = progress.add_task("", total=len(target_coins))
            
            # PÁRHUZAMOS FUTTATÁS
            tasks = [fetch_coin(coin, semaphore, progress, task) for coin in target_coins]
            results = await asyncio.gather(*tasks)

        market_data = [res for res in results if res is not None]

        # Táblázat felépítése
        table = Table(title="🔥 LIVE MARKET DATA & RISK ANALYSIS 🔥", border_style="green")
        table.add_column("Rank", justify="center", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Price (USD)", justify="right", style="green")
        table.add_column("24h Change", justify="right")
        table.add_column("Math Risk Score", justify="center")

        for coin in market_data:
            price = coin.get('market_data', {}).get('current_price', {}).get('usd', 0)
            change = coin.get('market_data', {}).get('price_change_percentage_24h', 0)
            score = coin.get('risk_score', 50)
            
            c_style = "green" if change > 0 else "red"
            r_style = "green" if score < 40 else ("yellow" if score < 70 else "red")
            
            table.add_row(
                str(coin.get('market_cap_rank', 'N/A')), 
                coin.get('name'), 
                f"${price:,.2f}", 
                f"[{c_style}]{change:.2f}%[/{c_style}]", 
                f"[{r_style}]{score:.0f}/100[/{r_style}]"
            )
            
        console.print(table)
        console.print("\n[dim]Tipp: Részletes elemzéshez használd: python -m src.main audit [token_neve][/dim]")

    asyncio.run(show_market())

@app.command()
def audit(token: str):
    """
    🛡️ Enterprise Deep Audit: AI, Kvantitatív elemzés, Hírek és Generatív PDF.
    """
    async def run_audit():
        console.rule(f"[bold red]ENTERPRISE DEEP AUDIT: {token.upper()}[/bold red]")
        
        with Progress(SpinnerColumn(), TextColumn("{task.description}"), transient=True) as progress:
            
            # 1. API ADATOK LETÖLTÉSE
            progress.add_task("[cyan]1/4 API adatok és Történelmi árak letöltése...", total=None)
            data = await cg_service.get_coin_data(token)
            
            if not data:
                console.print(f"[bold red]❌ A '{token}' token nem található, vagy API hiba történt![/bold red]")
                return
                
            historical_prices = await cg_service.get_historical_prices(data['id'], days=30)

            # 2. KVANTITATÍV ÉS OSINT ELEMZÉS
            progress.add_task("[blue]2/4 Algoritmikus Kockázatelemzés és Web OSINT...", total=None)
            
            # Kockázati Dimenziók (Matek)
            risk_data = risk_engine.calculate_risk_metrics(data)
            math_score = risk_data['quantitative_score']
            dimensions = risk_data['dimensions']
            
            # Párhuzamos RAG (Tudásbázis) és Hírek (Web Search) futtatása
            rag_task = asyncio.to_thread(rag.load_context)
            news_task = web_search.search_news(data['name'])
            context, latest_news = await asyncio.gather(rag_task, news_task)

            # 3. AI MOTOR (LLM)
            progress.add_task(f"[magenta]3/4 AI Generatív Elemzés ({settings.MODEL_NAME})...", total=None)
            
            # Ártrend számítása a prompthoz
            trend_info = "Not available"
            if historical_prices and len(historical_prices) > 7:
                start_price = historical_prices[0]
                end_price = historical_prices[-1]
                trend_pct = ((end_price - start_price) / start_price) * 100
                trend_info = f"30-Day Trend: {trend_pct:.2f}% (From ${start_price:.4f} to ${end_price:.4f})"

            desc = data.get('description', {}).get('en', '')[:1000]
            stats = f"Price: ${data['market_data']['current_price']['usd']}, ATH Change: {data['market_data']['ath_change_percentage']['usd']}%"

            system_prompt = (
                "You are a Senior Quant Risk Auditor. "
                "Detect SCAMS based on quantitative data, news, and knowledge base rules. "
                "Output STRICT JSON only."
            )
            
            user_prompt = (
                f"PROJECT: {data['name']}\n"
                f"OVERALL MATH RISK SCORE: {math_score}/100\n"
                f"DIMENSIONS (0-10, higher is safer): {dimensions}\n"
                f"PRICE ACTION: {trend_info}\n"
                f"STATS: {stats}\n"
                f"DESCRIPTION: {desc}\n\n"
                f"LATEST WEB NEWS: {latest_news}\n\n"
                f"KNOWLEDGE BASE RULES: {context}\n\n"
                "REQUIRED JSON OUTPUT STRUCTURE:\n"
                "{\n"
                '  "verdict": "Safe" or "Scam" or "High Risk",\n'
                '  "score": (int 0-100, combine math score with your judgment),\n'
                '  "summary": "Executive summary (max 3 sentences)",\n'
                '  "chart_analysis": "Write a 3-sentence technical analysis based on the PRICE ACTION and DIMENSIONS provided above.",\n'
                '  "pros": ["Strength 1", "Strength 2"],\n'
                '  "cons": ["Risk 1", "Risk 2"]\n'
                "}"
            )
            
            analysis = await llm.analyze_json(user_prompt, system_prompt)

            # 4. RIPORT KÉSZÍTÉS (PDF + Képek)
            progress.add_task("[green]4/4 PDF Riport és Grafikonok renderelése...", total=None)
            
            pdf_path = None
            if analysis and "error" not in analysis:
                pdf_path = ReportGenerator.create_pdf(
                    data=analysis, 
                    token_name=token, 
                    historical_prices=historical_prices, 
                    risk_dimensions=dimensions
                )

        # --- EREDMÉNY MEGJELENÍTÉSE ---
        if not analysis or "error" in analysis:
            console.print(f"[red]Hiba az AI elemzésben: {analysis.get('error', 'Unknown')}[/red]")
        else:
            verdict = analysis.get('verdict', 'Unknown')
            color = "green" if verdict == "Safe" else "red"
            
            console.print(Panel(
                f"[bold]Verdict: [{color}]{verdict}[/{color}][/bold]\n"
                f"Final Risk Score: {analysis.get('score')}/100 (Math Base: {math_score}/100)\n\n"
                f"[italic]{analysis.get('summary')}[/italic]\n\n"
                f"[bold]Trend Info:[/bold] {trend_info}",
                title=f"AUDIT SUCCESS: {token.upper()}", border_style=color
            ))

            if pdf_path:
                console.print(f"\n[bold green]✅ ENTERPRISE PDF RIPORT ELKÉSZÜLT:[/bold green] {pdf_path}")
                console.print("[dim]A riport tartalmazza a Trendvonalat (SMA indikátorral) és a Kockázati Radar ábrát.[/dim]")

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
            
            plan = await llm.analyze_json(user_prompt, system_prompt)

        if not plan or "error" in plan:
            console.print("[red]Hiba a generáláskor.[/red]")
        else:
            console.print(Panel(
                f"[bold]Stratégia:[/bold] {strategy.upper()}\n[bold]Indoklás:[/bold] {plan.get('reasoning')}",
                title="BEFEKTETÉSI TERV", border_style="blue"
            ))
            
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
            
            excel_path = ReportGenerator.export_to_excel(export_data, f"Portfolio_{strategy}")
            if excel_path:
                console.print(f"\n[cyan]📊 Excel exportálva: {excel_path}[/cyan]")

    asyncio.run(run_portfolio())

if __name__ == "__main__":
    app()