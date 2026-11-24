import json
from pathlib import Path
import runpy
import shutil
import sqlite3

import pytest
import requests
import yaml


SCRIPT = Path(__file__).resolve().parents[1] / 'src' / 'chemo_info_fetcher.py'
ASPIRIN = 'BSYNRYMUTXBXSQ'
CAFFEINE = 'RYYVLZVUVIJVGH'


@pytest.fixture
def enrichment(tmp_path, monkeypatch):
    script = tmp_path / 'module' / 'src' / SCRIPT.name
    script.parent.mkdir(parents=True)
    shutil.copyfile(SCRIPT, script)
    samples = tmp_path / 'samples'
    samples.mkdir()
    database = tmp_path / 'structures.db'
    parameters = tmp_path / 'params' / 'user.yml'
    parameters.parent.mkdir()
    parameters.write_text(yaml.safe_dump({
        'general': {'treated_data_path': str(samples)},
        'chemo-info-fetching': {'sql_db_path': str(tmp_path) + '/', 'sql_db_name': database.name, 'gnps_id': None},
    }))
    monkeypatch.chdir(tmp_path)

    def run(respond):
        def send(session, request, **options):
            response = requests.Response()
            response.url = request.url
            response.status_code, payload = respond(request)
            response._content = json.dumps(payload).encode()
            return response

        monkeypatch.setattr(requests.Session, 'send', send)
        runpy.run_path(str(script), run_name='__main__')

    return samples, database, run


def write_isdb(samples, connectivity_key):
    directory = samples / 'sample' / 'pos' / 'isdb'
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'sample_isdb_reweighted_flat_pos.tsv').write_text(
        'short_inchikey\tstructure_smiles_2D\tstructure_taxonomy_npclassifier_01pathway\t'
        'structure_taxonomy_npclassifier_02superclass\tstructure_taxonomy_npclassifier_03class\n'
        f'{connectivity_key}\tCC(=O)Oc1ccccc1C(=O)O\tunknown\tunknown\tunknown\n'
    )


@pytest.mark.parametrize('reply', [(503, {}), (200, {'error': 'query timed out'})])
def test_failed_lookup_does_not_write_negative_cache(enrichment, reply):
    samples, database, run = enrichment
    write_isdb(samples, ASPIRIN)
    with pytest.raises(RuntimeError, match='Wikidata'):
        run(lambda request: reply)
    assert not database.exists()


def test_retry_replaces_legacy_fallback_with_all_connectivity_matches(enrichment):
    samples, database, run = enrichment
    write_isdb(samples, ASPIRIN)
    run(lambda request: (200, {'results': {'bindings': []}}))
    with sqlite3.connect(database) as connection:
        assert connection.execute('SELECT inchikey, wikidata_id FROM structures_metadata').fetchone() == (
            'no_wikidata_match', 'no_wikidata_match')
        connection.execute('UPDATE structures_metadata SET inchikey = short_inchikey')
    original = database.read_bytes()
    with pytest.raises(RuntimeError, match='Wikidata'):
        run(lambda request: (503, {}))
    assert database.read_bytes() == original

    matches = [('Q18216', 'BSYNRYMUTXBXSQ-UHFFFAOYSA-N'), ('Q27108970', 'BSYNRYMUTXBXSQ-UHFFFAOYSA-M')]
    bindings = [{'wd': {'value': 'http://www.wikidata.org/entity/' + entity}, 'ik': {'value': full_key}}
                for entity, full_key in matches]
    run(lambda request: (200, {'results': {'bindings': bindings}}))
    with sqlite3.connect(database) as connection:
        rows = connection.execute('SELECT wikidata_id, inchikey, isomeric_smiles FROM structures_metadata').fetchall()
    assert sorted(rows) == [('http://www.wikidata.org/entity/' + entity, full_key, 'CC(=O)Oc1ccccc1C(=O)O')
                            for entity, full_key in matches]


@pytest.mark.parametrize('current_mode,legacy_mode', [('pos', 'neg'), ('neg', 'pos')])
def test_sirius_reports_contribute_distinct_keys_alongside_isdb(enrichment, current_mode, legacy_mode):
    samples, database, run = enrichment
    write_isdb(samples, ASPIRIN)
    ethanol = 'LFQSCWFLJHTTHZ'
    for mode, report, body in [
        (current_mode, 'structure_identifications.tsv', f'{CAFFEINE}\tCn1c(=O)c2c(ncn2C)n(C)c1=O\n{ASPIRIN}\tCC(=O)Oc1ccccc1C(=O)O\n'),
        (legacy_mode, 'compound_identifications.tsv', f'{ethanol}\tCCO\n'),
    ]:
        workspace = samples / 'sample' / mode / 'sample_WORKSPACE_SIRIUS'
        workspace.mkdir(parents=True)
        (workspace / report).write_text('InChIkey2D\tsmiles\n' + body)

    def respond(request):
        if request.url.startswith('https://npclassifier.ucsd.edu/'):
            return 200, {'pathway_results': [], 'superclass_results': [], 'class_results': []}
        return 200, {'results': {'bindings': []}}

    run(respond)
    with sqlite3.connect(database) as connection:
        keys = connection.execute('SELECT short_inchikey FROM structures_metadata ORDER BY short_inchikey').fetchall()
    assert keys == [(ASPIRIN,), (ethanol,), (CAFFEINE,)]
