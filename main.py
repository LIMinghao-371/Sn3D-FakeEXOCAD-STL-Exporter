from BatchExporter import BatchExporter

if __name__ == "__main__":
    exe_path = r"D:\DentalCAD Chemnitz\DentalCADApp\bin\DentalCADApp.exe"
    title_keyword = "exocad DentalCAD"
    root_path = r"E:\datas-2026-04-21-wangfei-xinghuowanfang-2-out\exocad"
    timeout = 60
    batchExporter = BatchExporter(exe_path, title_keyword, timeout)
    if batchExporter.init():
        batchExporter.start(root_path)
    # batchExporter.close()