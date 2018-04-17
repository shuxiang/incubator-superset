"""A collection of ORM sqlalchemy models for SQL Lab"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from datetime import datetime
import re

from flask import Markup
from flask_appbuilder import Model
from future.standard_library import install_aliases
import sqlalchemy as sqla
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text,
)
from sqlalchemy.orm import backref, relationship

from superset import sm
from superset.models.helpers import AuditMixinNullable
from superset.utils import QueryStatus

install_aliases()


class CompanyReportMap(Model):
    """ORM model for SQL query"""

    __tablename__ = 'company_report_map'
    id = Column(Integer, primary_key=True)
    company = Column(String(128))
    api_name = Column(String(256))
    report_id = Column(Integer)
    remark = Column(String(256))
