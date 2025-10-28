"""Excel读取工具"""
from typing import Dict, Any, List, Optional
from pathlib import Path
import csv

try:
    import openpyxl  # for .xlsx
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

try:
    import pandas as pd  # for .xls fallback
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from .ToolRegistry import BaseTool


class ExcelReaderTool(BaseTool):
    """读取 .xlsx/.xls/.csv 并输出每个sheet的结构化JSON"""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(
            name="excel_reader",
            description="读取Excel/CSV文件，输出结构化数据",
            config=config or {}
        )
        self.max_rows = int(self.config.get("max_rows", 10000))
        self.detect_header = bool(self.config.get("detect_header", True))

    async def process(self, input_data: Any) -> Dict[str, Any]:
        if isinstance(input_data, str):
            file_path = Path(input_data)
        else:
            raise ValueError("excel_reader 仅支持文件路径输入")

        if not file_path.exists():
            raise FileNotFoundError(str(file_path))

        suffix = file_path.suffix.lower()
        if suffix == ".csv":
            return self._read_csv(file_path)
        if suffix == ".xlsx":
            return self._read_xlsx(file_path)
        if suffix == ".xls":
            return self._read_xls(file_path)
        raise ValueError(f"不支持的文件格式: {suffix}")

    def _read_csv(self, path: Path) -> Dict[str, Any]:
        rows: List[List[Any]] = []
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                if i >= self.max_rows:
                    break
                rows.append(row)
        cells = []
        for r, row in enumerate(rows, start=1):
            for c, val in enumerate(row, start=1):
                cells.append({"r": r, "c": c, "value": val, "type": self._infer_type(val)})
        sheet = {
            "name": path.stem,
            "rows": len(rows),
            "cols": max((len(r) for r in rows), default=0),
            "cells": cells,
            "merged_ranges": []
        }
        return {"format": "csv", "sheets": [sheet], "summary": {"sheet_count": 1, "row_counts": [sheet["rows"]]}}

    def _read_xlsx(self, path: Path) -> Dict[str, Any]:
        if not OPENPYXL_AVAILABLE:
            raise RuntimeError("openpyxl 未安装，无法读取xlsx")
        wb = openpyxl.load_workbook(filename=str(path), data_only=True, read_only=True)
        sheets = []
        for ws in wb.worksheets:
            rows = []
            for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
                if i > self.max_rows:
                    break
                rows.append(list(row))
            cells = []
            for r, row in enumerate(rows, start=1):
                for c, val in enumerate(row, start=1):
                    cells.append({"r": r, "c": c, "value": val, "type": self._infer_type(val)})
            merged = []
            for mr in ws.merged_cells.ranges:
                merged.append(str(mr.bounds))
            sheets.append({
                "name": ws.title,
                "rows": len(rows),
                "cols": max((len(r) for r in rows), default=0),
                "cells": cells,
                "merged_ranges": merged
            })
        return {"format": "xlsx", "sheets": sheets, "summary": {"sheet_count": len(sheets), "row_counts": [s["rows"] for s in sheets]}}

    def _read_xls(self, path: Path) -> Dict[str, Any]:
        if not PANDAS_AVAILABLE:
            raise RuntimeError("pandas 未安装，无法读取xls")
        xls = pd.ExcelFile(str(path))
        sheets = []
        for name in xls.sheet_names:
            df = xls.parse(name, nrows=self.max_rows, header=0 if self.detect_header else None)
            rows = df.values.tolist()
            cells = []
            for r, row in enumerate(rows, start=1):
                for c, val in enumerate(row, start=1):
                    cells.append({"r": r, "c": c, "value": val, "type": self._infer_type(val)})
            sheets.append({
                "name": name,
                "rows": len(rows),
                "cols": df.shape[1] if rows else 0,
                "cells": cells,
                "merged_ranges": []
            })
        return {"format": "xls", "sheets": sheets, "summary": {"sheet_count": len(sheets), "row_counts": [s["rows"] for s in sheets]}}

    def _infer_type(self, val: Any) -> str:
        if val is None:
            return "null"
        if isinstance(val, bool):
            return "bool"
        if isinstance(val, (int, float)):
            return "number"
        return "string"
