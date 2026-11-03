from pathlib import Path
from streamlit.testing.v1 import AppTest

def test_dashboard_and_empty_selection():
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py")).run(timeout=30)
    assert not app.exception
    assert app.title[0].value == "Global AI Compute Monitor"
    assert app.metric[0].value == "6"
    app.multiselect[0].set_value([]).run()
    assert not app.exception
    assert any("Select at least one" in x.value for x in app.info)


def test_scenario_inputs_and_matching_scope():
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py")).run(timeout=30)
    for label,value in [("Installed accelerators (assumption)",10),("Matched-workload raw tokens/second/accelerator",100.),("Assumed completed demand tokens/day for this exact scope",100000.)]:
        next(w for w in app.number_input if w.label==label).set_value(value)
    for label,value in [("Defined workload ID (model, context, cache, precision, SLA)","test-workload"),("Geography for this scenario","US"),("Token accounting basis (input/output, modality)","text-total")]:
        next(w for w in app.text_input if w.label==label).set_value(value)
    app.run(timeout=30)
    assert not app.exception
    assert any(m.label=="Assumed demand / hypothetical capacity" for m in app.metric)
    assert len(app.tabs)==4
