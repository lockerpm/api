from shared.services.spreadsheet.spreadsheet import LockerSpreadSheet


def upgrade_survey_emails():
    spread_sheet = LockerSpreadSheet()
    spread_sheet.upgrade_survey_email()
