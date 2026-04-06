"""Internationalization (i18n) module for Chinese/English output."""

# Change this to "en" or "zh" to switch language
LANGUAGE = "zh"

# Translation dictionary
TRANSLATIONS = {
    "zh": {
        # display.py
        "no_trading_decisions": "无交易决策可用",
        "analysis_for": "分析结果",
        "agent_analysis": "代理分析",
        "trading_decision": "交易决策",
        "portfolio_summary": "投资组合摘要",
        "portfolio_strategy": "投资组合策略",
        "agent": "代理",
        "signal": "信号",
        "confidence": "置信度",
        "reasoning": "推理",
        "action": "操作",
        "quantity": "数量",
        "ticker": "股票代码",
        "bullish": "看涨",
        "bearish": "看跌",
        "neutral": "中性",
        "cash_balance": "现金余额",
        "total_position_value": "持仓总值",
        "total_value": "总价值",
        "portfolio_return": "组合收益率",
        "benchmark_return": "基准收益率",
        "sharpe_ratio": "夏普比率",
        "sortino_ratio": "索提诺比率",
        "max_drawdown": "最大回撤",
        "date": "日期",
        "price": "价格",
        "long_shares": "多头持仓",
        "short_shares": "空头持仓",
        "position_value": "持仓价值",
        "backtest_completed": "回测完成！",
        "backtest_interrupted": "回测被用户中断。",
        "partial_results": "有部分结果可用。",
        "initial_portfolio_value": "初始组合价值",
        "final_portfolio_value": "最终组合价值",
        "total_return": "总收益率",
        "could_not_generate_partial": "无法生成部分结果",
        # state.py
        "agent_reasoning_header": "代理推理",
        # llm.py
        "error_retry": "错误 - 重试",
        "llm_error": "LLM 调用 {max_retries} 次后失败",
        "analysis_error": "分析出错，使用默认值",
        "extract_json_error": "从响应中提取 JSON 时出错",
        # CLI prompts
        "space_select": "按空格键选择/取消选择分析师。",
        "press_enter_done": "\n\n按 'a' 切换全选。\n\n完成后按回车运行对冲基金。",
        "space_instruction": "\n\n说明：\n1. 按空格键选择/取消选择分析师。\n2. 按 'a' 切换全选。\n3. 完成后按回车。",
        "select_analysts": "选择您的 AI 分析师。",
        "select_ollama_model": "选择您的 Ollama 模型：",
        "select_llm_model": "选择您的 LLM 模型：",
        "enter_custom_model": "输入自定义模型名称：",
        "interrupt_exiting": "\n\n收到中断信号，正在退出...",
        "selected_analysts": "\n已选择的分析师",
        "using_ollama": "使用 Ollama 进行本地 LLM 推理。",
        "selected_ollama_model": "\n已选择 Ollama 模型",
        "selected_model": "\n已选择模型",
        "cannot_proceed_ollama": "没有 Ollama 和所选模型无法继续。",
        "model_not_found": "未找到模型 '{model_flag}'。请选择一个模型。",
        "engine_run_complete": "引擎运行完成",
        # backtesting/cli.py
        "run_backtesting": "运行回测模拟",
        "tickers_help": "以逗号分隔的股票代码（例如：AAPL,MSFT,GOOGL）",
        "analysts_help": "以逗号分隔的分析师（例如：michael_burry,other_analyst）",
        "analysts_all_help": "使用所有可用分析师（覆盖 --analysts）",
        "ollama_help": "使用 Ollama 进行本地 LLM 推理",
        "model_help": "要使用的模型名称（例如：gpt-4o）",
        "start_date_help": "开始日期（YYYY-MM-DD）",
        "end_date_help": "结束日期（YYYY-MM-DD）",
        "show_reasoning_help": "显示每个代理的推理",
        "show_agent_graph_help": "显示代理图",
        "start_date_format": "开始日期，格式 YYYY-MM-DD",
        "end_date_format": "结束日期，格式 YYYY-MM-DD",
        # Analyst descriptions (abbreviated for display)
        "analyst_order_prefix": "",
    },
}


def t(key: str, **kwargs) -> str:
    """Get translation for a key. Falls back to the key itself if not found."""
    lang_translations = TRANSLATIONS.get(LANGUAGE, {})
    value = lang_translations.get(key, key)
    if kwargs:
        try:
            return value.format(**kwargs)
        except (KeyError, IndexError):
            return value
    return value


def is_chinese() -> bool:
    """Check if the current language is Chinese."""
    return LANGUAGE == "zh"


# Language instruction prepended to LLM system prompts
LLM_LANGUAGE_INSTRUCTION = (
    "你必须在中文中回复。所有推理和理由必须使用简体中文。Return JSON only."
    if LANGUAGE == "zh"
    else ""
)
