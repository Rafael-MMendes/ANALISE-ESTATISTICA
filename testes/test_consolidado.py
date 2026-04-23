import app
print("Testing Consolidado 2026...")
try:
    df_cvp = app.load_data_cvp('CVP', 2026)
    print("CVP len:", len(df_cvp))
    df_mvi = app.load_data_mvi('MVI', 2026)
    print("MVI len:", len(df_mvi))
    df_tco = app.load_data_tco('TCO', 2026)
    print("TCO len:", len(df_tco))
    app.render_consolidado_module(2026)
    print("SUCCESS 2026")
except Exception as e:
    print(f"FAILED 2026: {e}")
