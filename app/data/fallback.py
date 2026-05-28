from .provider import DataProvider, StockData
from .akshare_provider import AkshareProvider
from .tushare_provider import TushareProvider
from .eastmoney_provider import EastmoneyProvider
from ..config import AppConfig


def _build_providers(config: AppConfig) -> list[DataProvider]:
    providers: list[DataProvider] = []
    for name in config.data.provider_order:
        if name == "tushare" and config.data.tushare.token:
            providers.append(TushareProvider(token=config.data.tushare.token))
        elif name == "akshare":
            providers.append(AkshareProvider())
        elif name == "eastmoney":
            providers.append(EastmoneyProvider())
    if not providers:
        providers.append(AkshareProvider())
    return providers


def fetch_stock_data(symbol: str, config: AppConfig) -> tuple[StockData, str]:
    """
    按配置的优先级依次尝试数据源。
    返回 (StockData, 实际使用的 provider_name)。
    若全部失败则抛出 RuntimeError。
    """
    providers = _build_providers(config)
    last_error = None

    for p in providers:
        if not p.is_available():
            continue
        try:
            data = p.fetch_all(symbol)
            if data.info.name or data.valuation.pe is not None:
                return data, p.name
        except Exception as e:
            last_error = e
            continue

    if last_error:
        raise RuntimeError(f"所有数据源均获取失败，最后错误: {last_error}")
    raise RuntimeError("没有可用的数据源，请在 config.yaml 中配置 tushare token 或检查网络连接")
