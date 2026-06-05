import { useEffect, useRef } from 'react'
import * as echarts from 'echarts'
import type { StockDaily } from '../types'

interface StockChartProps {
  data: StockDaily[]
  height?: number
}

const StockChart = ({ data, height = 400 }: StockChartProps) => {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)

  useEffect(() => {
    if (chartRef.current) {
      chartInstance.current = echarts.init(chartRef.current)
    }

    return () => {
      chartInstance.current?.dispose()
    }
  }, [])

  useEffect(() => {
    if (chartInstance.current && data.length > 0) {
      const dates = data.map((d) => d.date)
      const values = data.map((d) => [d.open, d.close, d.low, d.high])
      const volumes = data.map((d) => d.volume)

      const option: echarts.EChartsOption = {
        animation: false,
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross',
          },
        },
        grid: [
          {
            left: '10%',
            right: '8%',
            height: '50%',
          },
          {
            left: '10%',
            right: '8%',
            top: '63%',
            height: '16%',
          },
        ],
        xAxis: [
          {
            type: 'category',
            data: dates,
            boundaryGap: false,
            axisLine: { lineStyle: { color: '#777' } },
            min: 'dataMin',
            max: 'dataMax',
          },
          {
            type: 'category',
            gridIndex: 1,
            data: dates,
            boundaryGap: false,
            axisLine: { lineStyle: { color: '#777' } },
            min: 'dataMin',
            max: 'dataMax',
          },
        ],
        yAxis: [
          {
            scale: true,
            splitArea: {
              show: true,
            },
          },
          {
            scale: true,
            gridIndex: 1,
            splitNumber: 2,
            axisLabel: { show: false },
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: { show: false },
          },
        ],
        dataZoom: [
          {
            type: 'inside',
            xAxisIndex: [0, 1],
            start: 0,
            end: 100,
          },
          {
            show: true,
            xAxisIndex: [0, 1],
            type: 'slider',
            bottom: 10,
            start: 0,
            end: 100,
          },
        ],
        series: [
          {
            name: 'K线',
            type: 'candlestick',
            data: values,
            itemStyle: {
              color: '#ef232a',
              color0: '#14b143',
              borderColor: '#ef232a',
              borderColor0: '#14b143',
            },
          },
          {
            name: '成交量',
            type: 'bar',
            xAxisIndex: 1,
            yAxisIndex: 1,
            data: volumes,
          },
        ],
      }

      chartInstance.current.setOption(option)
    }
  }, [data])

  return <div ref={chartRef} style={{ height }} />
}

export default StockChart
