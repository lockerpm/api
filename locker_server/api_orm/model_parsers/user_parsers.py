from locker_server.api_orm.models import *
from locker_server.api_orm.models.users.education_emails import EducationEmailORM
from locker_server.core.entities.user.backup_credential import BackupCredential
from locker_server.core.entities.user.device import Device
from locker_server.core.entities.user.device_access_token import DeviceAccessToken
from locker_server.core.entities.user.education_email import EducationEmail
from locker_server.core.entities.user.exclude_domain import ExcludeDomain
from locker_server.core.entities.user.user import User
from locker_server.core.entities.user.user_score import UserScore


class UserParser:
    @classmethod
    def parse_user(cls, user_orm: UserORM) -> User:
        return User(
            user_id=user_orm.user_id,
            internal_id=user_orm.internal_id,
            creation_date=user_orm.creation_date,
            revision_date=user_orm.revision_date,
            first_login=user_orm.first_login,
            activated=user_orm.activated,
            activated_date=user_orm.activated_date,
            delete_account_date=user_orm.delete_account_date,
            account_revision_date=user_orm.account_revision_date,
            master_password=user_orm.master_password,
            master_password_hint=user_orm.master_password_hint,
            master_password_score=user_orm.master_password_score,
            security_stamp=user_orm.security_stamp,
            key=user_orm.key,
            public_key=user_orm.public_key,
            private_key=user_orm.private_key,
            kdf=user_orm.kdf,
            kdf_iterations=user_orm.kdf_iterations,
            api_key=user_orm.api_key,
            timeout=user_orm.timeout,
            timeout_action=user_orm.timeout_action,
            is_leaked=user_orm.is_leaked,
            use_relay_subdomain=user_orm.use_relay_subdomain,
            last_request_login=user_orm.last_request_login,
            login_failed_attempts=user_orm.login_failed_attempts,
            login_block_until=user_orm.login_block_until,
            login_method=user_orm.login_method,
            fd_credential_id=user_orm.fd_credential_id,
            fd_random=user_orm.fd_random,
            onboarding_process=user_orm.get_onboarding_process(),
            saas_source=user_orm.saas_source,
            email=user_orm.email,
            full_name=user_orm.full_name,
            language=user_orm.language,
            is_factor2=user_orm.is_factor2,
            base32_secret_factor2=user_orm.base32_secret_factor2,
            is_supper_admin=user_orm.is_supper_admin
        )

    @classmethod
    def parser_user_score(cls, user_score_orm: UserScoreORM) -> UserScore:
        return UserScore(
            user=cls.parse_user(user_orm=user_score_orm),
            cipher0=user_score_orm.cipher0,
            cipher1=user_score_orm.cipher1,
            cipher2=user_score_orm.cipher2,
            cipher3=user_score_orm.cipher3,
            cipher4=user_score_orm.cipher4,
            cipher5=user_score_orm.cipher5,
            cipher6=user_score_orm.cipher6,
            cipher7=user_score_orm.cipher7,
        )

    @classmethod
    def parse_device(cls, device_orm: DeviceORM) -> Device:
        return Device(
            device_id=device_orm.id,
            created_time=device_orm.created_time,
            refresh_token=device_orm.refresh_token,
            token_type=device_orm.token_type,
            scope=device_orm.scope,
            client_id=device_orm.client_id,
            device_name=device_orm.device_name,
            device_type=device_orm.device_type,
            device_identifier=device_orm.device_identifier,
            fcm_id=device_orm.fcm_id,
            last_login=device_orm.last_login,
            os=device_orm.get_os(),
            browser=device_orm.get_browser(),
            user=cls.parse_user(user_orm=device_orm.user)
        )

    @classmethod
    def parse_device_access_token(cls, device_access_token_orm: DeviceAccessTokenORM) -> DeviceAccessToken:
        return DeviceAccessToken(
            device_access_token_id=device_access_token_orm.id,
            access_token=device_access_token_orm.access_token,
            expired_time=device_access_token_orm.expired_time,
            grant_type=device_access_token_orm.grant_type,
            sso_token_id=device_access_token_orm.sso_token_id,
            device=cls.parse_device(device_orm=device_access_token_orm.device)
        )

    @classmethod
    def parse_exclude_domain(cls, exclude_domain_orm: ExcludeDomainORM) -> ExcludeDomain:
        return ExcludeDomain(
            exclude_domain_id=exclude_domain_orm.id,
            created_time=exclude_domain_orm.created_time,
            domain=exclude_domain_orm.domain,
            user=cls.parse_user(user_orm=exclude_domain_orm.user)
        )

    @classmethod
    def parse_education_email(cls, education_email_orm: EducationEmailORM) -> EducationEmail:
        return EducationEmail(
            education_email_id=education_email_orm.id,
            created_time=education_email_orm.created_time,
            email=education_email_orm.email,
            education_type=education_email_orm.education_type,
            university=education_email_orm.university,
            verified=education_email_orm.verified,
            verification_token=education_email_orm.verification_token,
            promo_code=education_email_orm.promo_code,
            user=cls.parse_user(user_orm=education_email_orm.user)
        )

    @classmethod
    def parse_backup_credential(cls, backup_credential_orm: BackupCredentialORM) -> BackupCredential:
        return BackupCredential(
            backup_credential_id=backup_credential_orm.id,
            creation_date=backup_credential_orm.creation_date,
            master_password=backup_credential_orm.master_password,
            master_password_hint=backup_credential_orm.master_password_hint,
            key=backup_credential_orm.key,
            public_key=backup_credential_orm.public_key,
            private_key=backup_credential_orm.private_key,
            fd_credential_id=backup_credential_orm.fd_credential_id,
            fd_random=backup_credential_orm.fd_random,
            kdf_iterations=backup_credential_orm.kdf_iterations,
            kdf=backup_credential_orm.kdf,
            user=cls.parse_user(user_orm=backup_credential_orm.user)
        )
