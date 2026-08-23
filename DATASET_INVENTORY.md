# UNdata 数据集与责任机构清单

分母来自 2026-08-21 官方 Sources catalog 的 36 个有序 datamart。变量数指来源原生元数据中登记并连接至 DataElement 与 Construct 的变量；“本次观测样本”指 2026-08-23 Storage 捕获尝试，不代表完整历史行数。

| Datamart | 数据集 | 发布/责任机构 | 已登记变量 | 本次观测样本 |
|---|---|---|---:|---|
| `ComTrade` | Commodity Trade Statistics Database | United Nations Statistics Division | 98 | 已获取 |
| `POP` | Demographic Statistics Database | United Nations Statistics Division | 111 | 已获取 |
| `EDATA` | Energy Statistics Database | United Nations Statistics Division | 2,740 | 已获取 |
| `ENV` | Environment Statistics Database | United Nations Statistics Division | 25 | 已获取 |
| `FAO` | FAOSTAT | Food and Agriculture Organization | 656 | 已获取 |
| `GenderStat` | Gender Info | United Nations Statistics Division | 116 | 已获取 |
| `GHG` | Greenhouse Gas Inventory Data | United Nations Framework Convention on Climate Change | 10 | 已获取 |
| `33` | Homicide Statistics | United Nations Office on Drugs and Crime | 2 | 未获取：45 秒超时 |
| `32` | Human Development Indices: A statistical update 2025 | United Nations Development Programme | 7 | 已获取 |
| `16` | Indicators on Women and Men | United Nations Statistics Division | 6 | 已获取 |
| `UNIDO` | INDSTAT | United Nations Industrial Development Organization | 760 | 已获取 |
| `ICS` | Industrial Commodity Statistics Database | United Nations Statistics Division | 620 | 已获取 |
| `IFS` | International Financial Statistics | International Monetary Fund | 76 | 已获取 |
| `30` | Key Indicators of the Labour Market, 7th Edition | International Labour Organization | 3 | 已获取 |
| `LABORSTA` | LABORSTA | International Labour Organization | 5 | 已获取 |
| `MDG` | Millennium Development Goals Database | United Nations Statistics Division | 126 | 未获取：官方端点 HTTP 500 |
| `SNAAMA` | National Accounts Estimates of Main Aggregates | United Nations Statistics Division | 72 | 已获取 |
| `SNA` | National Accounts Official Country Data | United Nations Statistics Division | 1,889 | 已获取 |
| `18` | OECD Data | Organisation for Economic Co-operation and Development | 4 | 已获取 |
| `SDGs` | Sustainable Development Goals Indicators | United Nations Statistics Division | 860 | 未获取：官方端点 HTTP 500 |
| `SOWC` | The State of the World’s Children | United Nations Children's Fund | 113 | 已获取 |
| `UNESCO` | UIS Data Centre | UNESCO Institute for Statistics | 288 | 已获取 |
| `UNAIDS` | UNAIDS Data | Joint United Nations Programme on HIV/AIDS | 44 | 已获取 |
| `UNHCR` | UNHCR Statistical Database | United Nations High Commissioner for Refugees | 1 | 已获取 |
| `KI` | United Nations Statistical Yearbook | United Nations Statistics Division | 33 | 未获取：45 秒超时 |
| `WHO` | WHO Data | World Health Organization | 216 | 已获取 |
| `29` | World Contraceptive Use | United Nations Population Division | 2 | 已获取 |
| `WDI` | World Development Indicators | The World Bank | 207 | 已获取 |
| `22` | World Fertility Data | United Nations Population Division | 3 | 已获取 |
| `25` | World Marriage Data | United Nations Population Division | 3 | 已获取 |
| `CLINO` | World Meteorological Organization Standard Normals | World Meteorological Organization | 86 | 已获取 |
| `PopDiv` | World Population Prospects: The 2024 Revision | United Nations Population Division | 85 | 已获取 |
| `WorldStat` | World Statistics Pocketbook | United Nations Statistics Division | 56 | 已获取 |
| `ITU` | World Telecommunication/ICT Indicators Database | International Telecommunications Union | 5 | 已获取 |
| `31` | World Telecommunication/ICT Indicators Table | International Telecommunications Union | 1 | 已获取 |
| `19` | World Tourism Data | World Tourism Organization | 5 | 已获取 |

## 观测捕获的严格含义

对 Explorer datamart，适配器按锁定的来源原生顺序选择第一个变量并调用官方导出；对出版物或替代路线，只获取一个官方承载观测的文件或表。完整请求、状态、文件 SHA-256、字节数和失败原因保存在 Release 与 Elements 的 `observations/bounded-official-exports/observation-capture-manifest.json` 中。
