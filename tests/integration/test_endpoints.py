# Copyright (c) 2018, Novo Nordisk Foundation Center for Biosustainability,
# Technical University of Denmark.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Test expected functioning of HTTP endpoints."""

from design_storage.models import Design


def test_docs(client):
    """Expect the OpenAPI docs to be served at root."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.content_type == "text/html; charset=utf-8"


def test_get_designs(client, session, design_fixtures):
    response = client.get("/designs")
    assert response.status_code == 200
    assert len(response.json) > 0


def test_get_public_designs(client, session, design_fixtures):
    response = client.get("/designs")
    assert all([m['project_id'] is None for m in response.json])


def test_get_design(client, session, design_fixtures):
    response = client.get(f"/designs/{design_fixtures[0].id}")
    assert response.status_code == 200


def test_get_design_not_found(client, session, design_fixtures):
    response = client.get("/designs/404")
    assert response.status_code == 404


def test_post_design(client, session, tokens):
    response = client.post(
        f"/designs",
        headers={
            'Authorization': f"Bearer {tokens['write']}",
        },
        json={
            'project_id': 1,
            'name': "Test design",
            'model_id': 1,
            'design': {
                "constraints": [{
                    "id": "FUM",
                    "lower_bound": 0,
                    "upper_bound": 0
                }],
                "gene_knockouts": ["b001"],
                "reaction_knockins": ["VANKpp"],
                "reaction_knockouts": ["SUCDi"],
            },
            'method': "Manual",
        },
    )
    assert response.status_code == 201


def test_put_design(client, session, design_fixtures, tokens):
    response = client.put(
        f"/designs/{design_fixtures[1].id}",
        headers={
            'Authorization': f"Bearer {tokens['write']}",
        },
        json={'id': 4, 'name': "Changed name"},
    )
    assert response.status_code == 204

    design = Design.query.filter(Design.id == design_fixtures[1].id).one()
    assert design.name == "Changed name"


def test_delete_design(client, session, design_fixtures, tokens):
    response = client.delete(f"/designs/{design_fixtures[1].id}", headers={
        'Authorization': f"Bearer {tokens['admin']}",
    })
    assert response.status_code == 204
