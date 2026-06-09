"""分析结果导出工具"""

import json
import csv
import io
from typing import Dict, Any, List
from datetime import datetime


class ResultExporter:
    """分析结果导出器"""

    @staticmethod
    def to_json(result: Dict[str, Any], pretty: bool = True) -> str:
        """导出为 JSON 格式"""
        export_data = {
            "export_time": datetime.now().isoformat(),
            "data": result
        }
        if pretty:
            return json.dumps(export_data, indent=2, ensure_ascii=False)
        return json.dumps(export_data, ensure_ascii=False)

    @staticmethod
    def to_csv(result: Dict[str, Any]) -> str:
        """导出为 CSV 格式（扁平化数据）"""
        output = io.StringIO()
        writer = csv.writer(output)

        # 写入表头
        writer.writerow(["Key", "Value"])

        # 扁平化并写入数据
        ResultExporter._flatten_and_write(writer, result, "")

        return output.getvalue()

    @staticmethod
    def _flatten_and_write(writer, data: Any, prefix: str):
        """递归扁平化数据"""
        if isinstance(data, dict):
            for key, value in data.items():
                new_key = f"{prefix}.{key}" if prefix else key
                ResultExporter._flatten_and_write(writer, value, new_key)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_key = f"{prefix}[{i}]"
                ResultExporter._flatten_and_write(writer, item, new_key)
        else:
            writer.writerow([prefix, data])

    @staticmethod
    def get_export_filename(plugin_name: str, symbol: str, format: str) -> str:
        """生成导出文件名"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{plugin_name}_{symbol}_{timestamp}.{format}"
