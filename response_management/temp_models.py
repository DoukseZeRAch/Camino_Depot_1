# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class BackupEmbeddingsTemp(models.Model):
    id = models.CharField(max_length=36)
    model_name = models.CharField(max_length=100, blank=True, null=True)
    model_version = models.CharField(max_length=50, blank=True, null=True)
    max_tokens = models.IntegerField(blank=True, null=True)
    is_active = models.IntegerField(blank=True, null=True)
    configuration = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'backup_embeddings_temp'


class BackupLog(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    backup_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=7, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'backup_log'


class BackupQuestionsTemp(models.Model):
    id = models.CharField(max_length=36)
    text = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=15, blank=True, null=True)
    category = models.CharField(max_length=50, blank=True, null=True)
    order_num = models.IntegerField(blank=True, null=True)
    is_active = models.IntegerField(blank=True, null=True)
    configuration = models.JSONField(blank=True, null=True)
    created_by = models.CharField(max_length=36, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'backup_questions_temp'


class ChunkRelations(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    chunk_source = models.ForeignKey('TextChunks', models.DO_NOTHING, blank=True, null=True)
    chunk_target = models.ForeignKey('TextChunks', models.DO_NOTHING, related_name='chunkrelations_chunk_target_set', blank=True, null=True)
    relation_type = models.CharField(max_length=50, blank=True, null=True)
    similarity_score = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'chunk_relations'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class EmbeddingModels(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    model_name = models.CharField(max_length=100, blank=True, null=True)
    model_version = models.CharField(max_length=50, blank=True, null=True)
    max_tokens = models.IntegerField(blank=True, null=True)
    is_active = models.IntegerField(blank=True, null=True)
    configuration = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'embedding_models'


class EmbeddingModelsBackup(models.Model):
    id = models.CharField(max_length=36)
    model_name = models.CharField(max_length=100, blank=True, null=True)
    model_version = models.CharField(max_length=50, blank=True, null=True)
    max_tokens = models.IntegerField(blank=True, null=True)
    is_active = models.IntegerField(blank=True, null=True)
    configuration = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'embedding_models_backup'


class PromptCache(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    prompt_type = models.CharField(max_length=50, blank=True, null=True)
    input_hash = models.CharField(max_length=255, blank=True, null=True)
    prompt_content = models.TextField(blank=True, null=True)
    response_content = models.TextField(blank=True, null=True)
    token_count = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    used_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'prompt_cache'


class Questions(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    text = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=15, blank=True, null=True)
    category = models.CharField(max_length=50, blank=True, null=True)
    order_num = models.IntegerField(blank=True, null=True)
    is_active = models.IntegerField(blank=True, null=True)
    configuration = models.JSONField(blank=True, null=True)
    created_by = models.ForeignKey('Users', models.DO_NOTHING, db_column='created_by', blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'questions'


class QuestionsBackup(models.Model):
    id = models.CharField(max_length=36)
    text = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=15, blank=True, null=True)
    category = models.CharField(max_length=50, blank=True, null=True)
    order_num = models.IntegerField(blank=True, null=True)
    is_active = models.IntegerField(blank=True, null=True)
    configuration = models.JSONField(blank=True, null=True)
    created_by = models.CharField(max_length=36, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'questions_backup'


class Responses(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    user = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)
    question = models.ForeignKey(Questions, models.DO_NOTHING, blank=True, null=True)
    content = models.JSONField(blank=True, null=True)
    is_complete = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    draft_data = models.JSONField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'responses'


class ResponsesBackup(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    response = models.ForeignKey(Responses, models.DO_NOTHING)
    user = models.ForeignKey('Users', models.DO_NOTHING)
    question = models.ForeignKey(Questions, models.DO_NOTHING)
    content = models.JSONField()
    is_complete = models.IntegerField(blank=True, null=True)
    backup_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'responses_backup'


class RoadmapVersions(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    roadmap = models.ForeignKey('Roadmaps', models.DO_NOTHING, blank=True, null=True)
    version_number = models.IntegerField(blank=True, null=True)
    content = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'roadmap_versions'


class Roadmaps(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    user = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)
    title = models.CharField(max_length=200, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'roadmaps'


class TextChunks(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    source_type = models.CharField(max_length=8, blank=True, null=True)
    source_id = models.CharField(max_length=36, blank=True, null=True)
    chunk_index = models.IntegerField(blank=True, null=True)
    chunk_content = models.TextField(blank=True, null=True)
    token_count = models.IntegerField(blank=True, null=True)
    embedding = models.ForeignKey('TextEmbeddings', models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'text_chunks'


class TextChunksBackup(models.Model):
    id = models.CharField(max_length=36)
    source_type = models.CharField(max_length=8, blank=True, null=True)
    source_id = models.CharField(max_length=36, blank=True, null=True)
    chunk_index = models.IntegerField(blank=True, null=True)
    chunk_content = models.TextField(blank=True, null=True)
    token_count = models.IntegerField(blank=True, null=True)
    embedding_id = models.CharField(max_length=36, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'text_chunks_backup'


class TextEmbeddings(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    text_content = models.TextField(blank=True, null=True)
    embedding_vector = models.JSONField(blank=True, null=True)
    model_version = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'text_embeddings'


class TextEmbeddingsBackup(models.Model):
    id = models.CharField(max_length=36)
    text_content = models.TextField(blank=True, null=True)
    embedding_vector = models.JSONField(blank=True, null=True)
    model_version = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'text_embeddings_backup'


class TokenBlacklistBlacklistedtoken(models.Model):
    id = models.BigAutoField(primary_key=True)
    blacklisted_at = models.DateTimeField()
    token = models.OneToOneField('TokenBlacklistOutstandingtoken', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'token_blacklist_blacklistedtoken'


class TokenBlacklistOutstandingtoken(models.Model):
    id = models.BigAutoField(primary_key=True)
    token = models.TextField()
    created_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField()
    user = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)
    jti = models.CharField(unique=True, max_length=255)

    class Meta:
        managed = False
        db_table = 'token_blacklist_outstandingtoken'


class Users(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    email = models.CharField(unique=True, max_length=255, blank=True, null=True)
    username = models.CharField(max_length=100, blank=True, null=True)
    password_hash = models.CharField(max_length=255)
    role = models.CharField(max_length=7)
    is_active = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    last_login = models.DateTimeField(blank=True, null=True)
    is_anonymous = models.IntegerField()
    is_authenticated = models.IntegerField()
    date_joined = models.DateTimeField()
    first_name = models.CharField(max_length=150)
    is_staff = models.IntegerField()
    is_superuser = models.IntegerField()
    last_name = models.CharField(max_length=150)
    password = models.CharField(max_length=128)

    class Meta:
        managed = False
        db_table = 'users'


class UsersGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    users = models.ForeignKey(Users, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'users_groups'
        unique_together = (('users', 'group'),)


class UsersUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    users = models.ForeignKey(Users, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'users_user_permissions'
        unique_together = (('users', 'permission'),)


class VectorizationJobs(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    source_type = models.CharField(max_length=8, blank=True, null=True)
    source_id = models.CharField(max_length=36, blank=True, null=True)
    status = models.CharField(max_length=10, blank=True, null=True)
    model = models.ForeignKey(EmbeddingModels, models.DO_NOTHING, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vectorization_jobs'
