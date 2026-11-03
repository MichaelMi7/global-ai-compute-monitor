from pathlib import Path
from streamlit.testing.v1 import AppTest

def test_dashboard_and_empty_selection():
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py")).run(timeout=30)
    assert not app.exception
    assert app.title[0].value == "Global AI Compute Monitor"
    assert app.metric[0].value == "3"
    app.multiselect[0].set_value([]).run()
    assert not app.exception
    assert any("Select at least one" in x.value for x in app.info)
