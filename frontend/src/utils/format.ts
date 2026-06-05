/**
 * 格式化数字
 */
export function formatNumber(num: number, decimals: number = 2): string {
  return num.toFixed(decimals)
}

/**
 * 格式化百分比
 */
export function formatPercent(num: number, decimals: number = 2): string {
  return `${(num * 100).toFixed(decimals)}%`
}

/**
 * 格式化金额
 */
export function formatAmount(num: number): string {
  if (num >= 100000000) {
    return `${(num / 100000000).toFixed(2)}亿`
  }
  if (num >= 10000) {
    return `${(num / 10000).toFixed(2)}万`
  }
  return num.toFixed(2)
}

/**
 * 格式化日期
 */
export function formatDate(date: string | Date): string {
  const d = new Date(date)
  return d.toLocaleDateString('zh-CN')
}

/**
 * 格式化时间
 */
export function formatTime(date: string | Date): string {
  const d = new Date(date)
  return d.toLocaleTimeString('zh-CN')
}

/**
 * 格式化日期时间
 */
export function formatDateTime(date: string | Date): string {
  const d = new Date(date)
  return d.toLocaleString('zh-CN')
}

/**
 * 获取涨跌颜色
 */
export function getChangeColor(change: number): string {
  if (change > 0) return '#ef232a'
  if (change < 0) return '#14b143'
  return '#000000'
}

/**
 * 获取信号颜色
 */
export function getSignalColor(signal: string): string {
  switch (signal) {
    case 'buy':
      return '#ef232a'
    case 'sell':
      return '#14b143'
    default:
      return '#1890ff'
  }
}

/**
 * 获取信号文本
 */
export function getSignalText(signal: string): string {
  switch (signal) {
    case 'buy':
      return '买入'
    case 'sell':
      return '卖出'
    default:
      return '持有'
  }
}

/**
 * 获取趋势颜色
 */
export function getTrendColor(trend: string): string {
  switch (trend) {
    case 'bullish':
      return '#ef232a'
    case 'bearish':
      return '#14b143'
    default:
      return '#1890ff'
  }
}

/**
 * 获取趋势文本
 */
export function getTrendText(trend: string): string {
  switch (trend) {
    case 'bullish':
      return '看多'
    case 'bearish':
      return '看空'
    default:
      return '震荡'
  }
}
