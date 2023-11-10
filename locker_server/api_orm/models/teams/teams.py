from locker_server.api_orm.abstracts.teams.teams import AbstractTeamORM
from locker_server.shared.utils.app import now, random_n_digit


class TeamORM(AbstractTeamORM):
    class Meta(AbstractTeamORM.Meta):
        swappable = 'LS_TEAM_MODEL'
        db_table = 'cs_teams'

    @classmethod
    def create(cls, **data):
        name = data.get("name")
        description = data.get("description", "")
        creation_date = data.get("creation_date", now())
        personal_share = data.get("personal_share", False)
        team_id = data.get("id")
        if not team_id:
            # Create new team object
            while True:
                team_id = random_n_digit(n=6)
                if cls.objects.filter(id=team_id).exists() is False:
                    break
        new_team = cls(
            id=team_id, name=name, description=description, creation_date=creation_date, personal_share=personal_share
        )
        new_team.save()

        # Create team members here
        members = data.get("members", [])
        new_team.team_members.model.create_multiple(new_team.id, *members)

        return new_team
