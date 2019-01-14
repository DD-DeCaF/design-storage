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

"""Implement RESTful API endpoints using resources."""

from flask import abort, g, make_response
from flask_apispec import MethodResource, marshal_with, use_kwargs
from flask_apispec.extension import FlaskApiSpec
from sqlalchemy.orm.exc import NoResultFound

from .jwt import jwt_require_claim, jwt_required
from .models import Design, db
from .schemas import DesignBaseSchema


def init_app(app):
    """Register API resources on the provided Flask application."""
    def register(path, resource):
        app.add_url_rule(path, view_func=resource.as_view(resource.__name__))
        docs.register(resource, endpoint=resource.__name__)

    docs = FlaskApiSpec(app)
    app.add_url_rule('/healthz', healthz.__name__, healthz)
    register('/designs', DesignsResource)
    register('/designs/<int:design_id>', DesignResource)


def healthz():
    """Return an empty, successful response for readiness checks."""
    # Verify that the database connection is alive.
    db.session.execute('select version()').fetchall()
    return ""


class DesignsResource(MethodResource):
    """Design collection resource."""

    @marshal_with(DesignBaseSchema(many=True))
    def get(self):
        return Design.query.filter(
            Design.project_id.in_(g.jwt_claims['prj']) |  # noqa: W504
            Design.project_id.is_(None)
        ).all()

    @use_kwargs(DesignBaseSchema(exclude=('id',)))
    @marshal_with(DesignBaseSchema, code=201)
    @jwt_required
    def post(self, **payload):
        design = Design(**payload)
        jwt_require_claim(payload['project_id'], 'write')
        db.session.add(design)
        db.session.commit()
        return {'id': design.id}


class DesignResource(MethodResource):
    """Single design resource."""

    @marshal_with(DesignBaseSchema, code=200)
    def get(self, design_id):
        try:
            return Design.query.filter(
                Design.id == design_id,
            ).filter(
                Design.project_id.in_(g.jwt_claims['prj']) |  # noqa: W504
                Design.project_id.is_(None)
            ).one()
        except NoResultFound:
            abort(404, f"Cannot find design with id {design_id}")

    @use_kwargs(DesignBaseSchema(exclude=('id',), partial=True))
    @marshal_with(None, code=204)
    @jwt_required
    def put(self, design_id, **payload):
        try:
            design = Design.query.filter(
                Design.id == design_id,
            ).filter(
                Design.project_id.in_(g.jwt_claims['prj']) |  # noqa: W504
                Design.project_id.is_(None)
            ).one()
        except NoResultFound:
            abort(404, f"Cannot find design with id {design_id}")
        else:
            jwt_require_claim(design.project_id, 'write')
            for key, value in payload.items():
                setattr(design, key, value)
            db.session.commit()
            return make_response('', 204)

    @marshal_with(None, code=204)
    @jwt_required
    def delete(self, design_id):
        try:
            design = Design.query.filter(
                Design.id == design_id,
            ).filter(
                Design.project_id.in_(g.jwt_claims['prj']) |  # noqa: W504
                Design.project_id.is_(None)
            ).one()
        except NoResultFound:
            abort(404, f"Cannot find design with id {design_id}")
        else:
            jwt_require_claim(design.project_id, 'admin')
            db.session.delete(design)
            db.session.commit()
            return make_response('', 204)
