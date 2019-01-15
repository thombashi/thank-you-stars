# encoding: utf-8

from __future__ import unicode_literals


def get_github_repo_id(repository):
    return "{}/{}".format(repository.owner.login, repository.name)
