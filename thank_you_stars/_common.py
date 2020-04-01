def get_github_repo_id(repository):
    return "{}/{}".format(repository.owner.login, repository.name)
