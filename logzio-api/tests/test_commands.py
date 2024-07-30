import json
import pytest
import requests_mock
from click.testing import CliRunner
from commands.commands import create_sub_account, create_api_key, create_metric_account, create_grafana_folder, get_all_grafana_data_sources, get_dashboard_by_uuid, create_dashboard

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def mock_requests():
    with requests_mock.Mocker() as m:
        yield m

def test_create_sub_account(runner, mock_requests):
    mock_requests.post('https://api.logz.io/v1/account-management/time-based-accounts', json={"accountId": 99999})
    
    result = runner.invoke(create_sub_account, [
        '--account-name', 'test_account',
        '--email', 'test@example.com',
        '--retention-days', '30',
        '--sharing-objects-accounts', 'test_account',
        '--is-flexible', 'True',
        '--reserved-daily-gb', '1',
        '--maxdaily-gb', '2',
        '--searchable', 'True',
        '--accessible', 'True',
        '--doc-size-setting', 'True',
        '--utilization-settings', 'default'
    ])
    assert result.exit_code == 0
    assert '99999' in result.output

def test_create_api_key(runner, mock_requests):
    mock_requests.post('https://api.logz.io/v1/api-tokens/sub-account', json={
        "id": 7386,
        "name": "newTokenTest999",
        "token": "c498fbc3-a3ac-4676-ad09-689854b5cbbd",
        "createdAt": 1621858311
    })
    
    result = runner.invoke(create_api_key, [
        '--name', 'test_key',
        '--account-id', '12345'
    ])
    assert result.exit_code == 0
    assert 'c498fbc3-a3ac-4676-ad09-689854b5cbbd' in result.output

def test_create_metric_account(runner, mock_requests):
    mock_requests.post('https://api.logz.io/v1/account-management/metrics-accounts', json={
        "id": 99999,
        "accountName": "test_metrics",
        "token": "some-token",
        "createdAt": "2024-06-13T11:13:42.870Z",
        "planUts": 100,
        "authorizedAccountsIds": [
            12345, 67890
        ]
    })
    
    result = runner.invoke(create_metric_account, [
        '--email', 'test@example.com',
        '--account-name', 'test_metrics',
        '--plan-uts', '100',
        '--authorized-accounts-ids', '12345,67890'
    ])
    assert result.exit_code == 0
    assert '99999' in result.output
    assert 'test_metrics' in result.output
    assert 'some-token' in result.output
    assert '2024-06-13T11:13:42.870Z' in result.output
    
def test_create_grafana_folder(runner, mock_requests):
    mock_requests.post('https://api.logz.io/v1/grafana/api/folders', json={"uid": "test_uid"})
    
    result = runner.invoke(create_grafana_folder, [
        '--title', 'test_folder'
    ])
    assert result.exit_code == 0
    assert 'test_uid' in result.output
    
def test_get_all_grafana_data_sources(runner, mock_requests):
    mock_response = [
        {
            "id": 123,
            "uid": "DCFaFyDnk",
            "name": "cluster6_metrics",
            "type": "prometheus",
            "database": 123456
        }
    ]
    mock_requests.get('https://api.logz.io/v1/grafana/api/datasources/summary', json=mock_response)
    
    result = runner.invoke(get_all_grafana_data_sources)
    assert result.exit_code == 0
    assert 'cluster6_metrics' in result.output
    assert 'DCFaFyDnk' in result.output
    assert 'prometheus' in result.output
    assert '123456' in result.output


def test_get_dashboard_by_uuid(runner, mock_requests):
    mock_response = {
        "dashboard": {
            "id": 1,
            "uid": "56c2b472-dda4-4799-bc42-c27fa04f33bf",
            "title": "Production Overview",
            "tags": ["tag3"],
            "timezone": "browser",
            "schemaVersion": 1,
            "version": 0
        },
        "meta": {
            "isStarred": True,
            "url": "/d/cIBgcSjkk/production-overview",
            "folderId": 2,
            "folderUid": "l3KqBxCMz",
            "slug": "production-overview"
        }
    }
    mock_requests.get('https://api.logz.io/v1/grafana/api/dashboards/uid/56c2b472-dda4-4799-bc42-c27fa04f33bf', json=mock_response)
    
    result = runner.invoke(get_dashboard_by_uuid, ['56c2b472-dda4-4799-bc42-c27fa04f33bf'])
    assert result.exit_code == 0
    assert 'Production Overview' in result.output
    assert 'tag3' in result.output
    assert 'browser' in result.output
    assert '1' in result.output
    assert '0' in result.output
    assert 'isStarred' in result.output
    assert 'production-overview' in result.output
    assert '56c2b472-dda4-4799-bc42-c27fa04f33bf' in result.output


def test_create_dashboard(runner, mock_requests):
    mock_response = {
        "id": 1,
        "uid": "cIBgcSjkk",
        "url": "/d/cIBgcSjkk/production-overview",
        "status": "success",
        "version": 1,
        "slug": "production-overview"
    }
    mock_requests.post('https://api.logz.io/v1/grafana/api/dashboards/db', json=mock_response)
    
    result = runner.invoke(create_dashboard, [
        '--dashboard-title', 'test_dashboard'
    ])
    assert result.exit_code == 0
    assert 'cIBgcSjkk' in result.output
    assert 'success' in result.output
    assert 'production-overview' in result.output
    assert '1' in result.output

