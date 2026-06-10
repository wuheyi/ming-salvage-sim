# Extractor 全字段覆盖测试报告

- 跑 case：**29**　PASS **29** / FAIL **0** / ERROR **0**
- 顶层字段总数：**22**
- 耗时：847s

## 一、字段遗漏校验

⚠️ **无任何 case 验证的字段（17）**：钱粮收支、财政制度变化、裁撤月度收支、局势推进、新立局势、撤销局势、结案局势、军队变化、新建军队、军备变化、势力变化、四方动向、人物变化、后宫册封、密令进度、密令结案、崇祯结局

❌ **有 case 期望但实测从未抽到的字段（10）**：财政制度变化、裁撤月度收支、撤销局势、结案局势、军备变化、人物变化、后宫册封、密令进度、密令结案、崇祯结局　← 需排查 prompt 或 case

## 二、字段覆盖矩阵

| 顶层字段 | 期望次数 | 实测命中次数 | 命中 case |
|---|---|---|---|
| ✅ 国势变化 | 2 | 10 | c228_diqu_wangtian、c229_diqu_huangzhuang、c230_diqu_tianfuli、c231_diqu_liaoxiangli、c240_diqu_kongzhi、c200_guoshi_minxin… |
| ✅ 钱粮收支 | 0 | 4 | c220_diqu_minxin、c221_diqu_dongluan、c211_jieji_nongmin、c200_guoshi_minxin |
| — 财政制度变化 | 0 | 0 |  |
| ✅ 新立月度收支 | 4 | 4 | c205_xinli_guanmin、c206_xinli_huangzhuang、c207_xinli_wangtian、c208_xinli_yintian |
| — 裁撤月度收支 | 0 | 0 |  |
| ✅ 派系变化 | 1 | 7 | c228_diqu_wangtian、c229_diqu_huangzhuang、c240_diqu_kongzhi、c209_paixi_sat、c205_xinli_guanmin、c207_xinli_wangtian… |
| ✅ 阶级变化 | 1 | 24 | c220_diqu_minxin、c221_diqu_dongluan、c222_diqu_liangchan、c223_diqu_cunliang、c224_diqu_shenshen、c226_diqu_fubai… |
| ✅ 地区变化 | 21 | 23 | c220_diqu_minxin、c221_diqu_dongluan、c222_diqu_liangchan、c223_diqu_cunliang、c224_diqu_shenshen、c225_diqu_junshi… |
| ✅ 局势推进 | 0 | 29 | c220_diqu_minxin、c221_diqu_dongluan、c222_diqu_liangchan、c223_diqu_cunliang、c224_diqu_shenshen、c225_diqu_junshi… |
| ✅ 新立局势 | 0 | 4 | c240_diqu_kongzhi、c201_guoshi_huangwei、c205_xinli_guanmin、c207_xinli_wangtian |
| — 撤销局势 | 0 | 0 |  |
| — 结案局势 | 0 | 0 |  |
| ✅ 军队变化 | 0 | 8 | c221_diqu_dongluan、c225_diqu_junshi、c230_diqu_tianfuli、c231_diqu_liaoxiangli、c237_diqu_shuishou、c238_diqu_tianzai… |
| ✅ 新建军队 | 0 | 1 | c221_diqu_dongluan |
| — 军备变化 | 0 | 0 |  |
| ✅ 势力变化 | 0 | 7 | c221_diqu_dongluan、c230_diqu_tianfuli、c231_diqu_liaoxiangli、c237_diqu_shuishou、c238_diqu_tianzai、c240_diqu_kongzhi… |
| ✅ 四方动向 | 0 | 8 | c221_diqu_dongluan、c225_diqu_junshi、c230_diqu_tianfuli、c231_diqu_liaoxiangli、c237_diqu_shuishou、c238_diqu_tianzai… |
| — 人物变化 | 0 | 0 |  |
| — 后宫册封 | 0 | 0 |  |
| — 密令进度 | 0 | 0 |  |
| — 密令结案 | 0 | 0 |  |
| — 崇祯结局 | 0 | 0 |  |

## 三、逐 case 明细

| case | 状态 | 期望 | 实测命中 | 缺失 | 多余 | 备注 |
|---|---|---|---|---|---|---|
| c220_diqu_minxin | ✅ | 地区变化 | 地区变化、局势推进、钱粮收支、阶级变化 | — | 局势推进、钱粮收支、阶级变化 |  |
| c221_diqu_dongluan | ✅ | 地区变化 | 军队变化、势力变化、四方动向、地区变化、局势推进、新建军队、钱粮收支、阶级变化 | — | 军队变化、势力变化、四方动向、局势推进、新建军队、钱粮收支、阶级变化 |  |
| c222_diqu_liangchan | ✅ | 地区变化 | 地区变化、局势推进、阶级变化 | — | 局势推进、阶级变化 |  |
| c223_diqu_cunliang | ✅ | 地区变化 | 地区变化、局势推进、阶级变化 | — | 局势推进、阶级变化 |  |
| c224_diqu_shenshen | ✅ | 地区变化 | 地区变化、局势推进、阶级变化 | — | 局势推进、阶级变化 |  |
| c225_diqu_junshi | ✅ | 地区变化 | 军队变化、四方动向、地区变化、局势推进 | — | 军队变化、四方动向、局势推进 |  |
| c226_diqu_fubai | ✅ | 地区变化 | 地区变化、局势推进、阶级变化 | — | 局势推进、阶级变化 |  |
| c227_diqu_guanmintian | ✅ | 地区变化 | 地区变化、局势推进、阶级变化 | — | 局势推进、阶级变化 |  |
| c228_diqu_wangtian | ✅ | 地区变化 | 国势变化、地区变化、局势推进、派系变化、阶级变化 | — | 国势变化、局势推进、派系变化、阶级变化 |  |
| c229_diqu_huangzhuang | ✅ | 地区变化 | 国势变化、地区变化、局势推进、派系变化、阶级变化 | — | 国势变化、局势推进、派系变化、阶级变化 |  |
| c230_diqu_tianfuli | ✅ | 地区变化 | 军队变化、势力变化、四方动向、国势变化、地区变化、局势推进、阶级变化 | — | 军队变化、势力变化、四方动向、国势变化、局势推进、阶级变化 |  |
| c231_diqu_liaoxiangli | ✅ | 地区变化 | 军队变化、势力变化、四方动向、国势变化、地区变化、局势推进、阶级变化 | — | 军队变化、势力变化、四方动向、国势变化、局势推进、阶级变化 |  |
| c232_diqu_yanshui | ✅ | 地区变化 | 地区变化、局势推进、阶级变化 | — | 局势推进、阶级变化 |  |
| c233_diqu_shangshui | ✅ | 地区变化 | 地区变化、局势推进 | — | 局势推进 |  |
| c234_diqu_renkou | ✅ | 地区变化 | 地区变化、局势推进、阶级变化 | — | 局势推进、阶级变化 |  |
| c235_diqu_tianmu | ✅ | 地区变化 | 地区变化、局势推进、阶级变化 | — | 局势推进、阶级变化 |  |
| c236_diqu_yintian | ✅ | 地区变化 | 地区变化、局势推进、阶级变化 | — | 局势推进、阶级变化 |  |
| c237_diqu_shuishou | ✅ | 地区变化 | 军队变化、势力变化、四方动向、地区变化、局势推进、阶级变化 | — | 军队变化、势力变化、四方动向、局势推进、阶级变化 |  |
| c238_diqu_tianzai | ✅ | 地区变化 | 军队变化、势力变化、四方动向、地区变化、局势推进、阶级变化 | — | 军队变化、势力变化、四方动向、局势推进、阶级变化 |  |
| c239_diqu_renhuo | ✅ | 地区变化 | 地区变化、局势推进、阶级变化 | — | 局势推进、阶级变化 |  |
| c240_diqu_kongzhi | ✅ | 地区变化 | 军队变化、势力变化、四方动向、国势变化、地区变化、局势推进、新立局势、派系变化、阶级变化 | — | 军队变化、势力变化、四方动向、国势变化、局势推进、新立局势、派系变化、阶级变化 |  |
| c209_paixi_sat | ✅ | 派系变化 | 局势推进、派系变化 | — | 局势推进 |  |
| c211_jieji_nongmin | ✅ | 阶级变化 | 军队变化、势力变化、四方动向、地区变化、局势推进、钱粮收支、阶级变化 | — | 军队变化、势力变化、四方动向、地区变化、局势推进、钱粮收支 |  |
| c200_guoshi_minxin | ✅ | 国势变化 | 国势变化、地区变化、局势推进、钱粮收支、阶级变化 | — | 地区变化、局势推进、钱粮收支、阶级变化 |  |
| c201_guoshi_huangwei | ✅ | 国势变化 | 国势变化、局势推进、新立局势 | — | 局势推进、新立局势 |  |
| c205_xinli_guanmin | ✅ | 新立月度收支 | 国势变化、局势推进、新立局势、新立月度收支、派系变化、阶级变化 | — | 国势变化、局势推进、新立局势、派系变化、阶级变化 |  |
| c206_xinli_huangzhuang | ✅ | 新立月度收支 | 局势推进、新立月度收支 | — | 局势推进 |  |
| c207_xinli_wangtian | ✅ | 新立月度收支 | 国势变化、局势推进、新立局势、新立月度收支、派系变化、阶级变化 | — | 国势变化、局势推进、新立局势、派系变化、阶级变化 |  |
| c208_xinli_yintian | ✅ | 新立月度收支 | 国势变化、局势推进、新立月度收支、派系变化、阶级变化 | — | 国势变化、局势推进、派系变化、阶级变化 |  |
