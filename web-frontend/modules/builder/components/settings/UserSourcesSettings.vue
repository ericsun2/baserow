<template>
  <!-- Show user source list -->
  <div
    v-if="!showCreateForm && editedUserSource === null"
    class="user-sources-settings"
  >
    <h2 class="box__title">{{ $t('userSourceSettings.titleOverview') }}</h2>
    <Error :error="error"></Error>
    <div v-if="!error.visible" class="actions actions--right">
      <Button prepend-icon="baserow-icon-plus" @click="showForm()">
        {{ $t('userSourceSettings.addUserSource') }}
      </Button>
    </div>
    <div
      v-if="$fetchState.pending && !error.visible"
      class="user-source-settings__loader"
    />
    <template v-else>
      <div
        v-for="userSource in userSources"
        :key="userSource.id"
        class="user-source-settings__user-source"
        @delete="deleteUserSource(userSource)"
      >
        <Presentation
          :image="getUserSourceType(userSource).image"
          :title="userSource.name"
          :subtitle="getUserSourceType(userSource).getSummary(userSource)"
          avatar-color="ghost"
          style="flex: 1"
        />
        <div class="user-source-settings__user-source-actions">
          <Button
            icon="iconoir-edit"
            type="light"
            @click="showForm(userSource)"
          />
          <Button
            icon="iconoir-trash"
            type="light"
            @click="deleteUserSource(userSource)"
          />
        </div>
      </div>
    </template>
    <p
      v-if="!error.visible && !$fetchState.pending && userSources.length === 0"
      class="margin-top-3"
    >
      {{ $t('userSourceSettings.noUserSourceMessage') }}
    </p>
  </div>
  <!-- Edit user source -->
  <div v-else-if="editedUserSource">
    <h2 class="box__title">
      {{ $t('userSourceSettings.titleUpdateUserSource') }}
    </h2>
    <Error :error="error"></Error>

    <Presentation
      :image="getUserSourceType(editedUserSource).image"
      :title="getUserSourceType(editedUserSource).name"
      avatar-color="ghost"
      style="flex: 1; margin-bottom: 18px"
      icon-size="tiny"
    />

    <UpdateUserSourceForm
      ref="userSourceForm"
      :builder="builder"
      :integrations="integrations"
      :user-source-type="getUserSourceType(editedUserSource)"
      :default-values="editedUserSource"
      @submitted="updateUserSource"
      @values-changed="onValueChange"
    />
    <div class="actions">
      <Button
        type="link"
        prepend-icon="iconoir-nav-arrow-left"
        @click="editedUserSource = null"
      >
        {{ $t('action.back') }}
      </Button>
      <Button
        :disabled="actionInProgress || invalidForm"
        :loading="actionInProgress"
        size="large"
        @click="$refs.userSourceForm.submit()"
      >
        {{ $t('action.save') }}
      </Button>
    </div>
  </div>
  <!-- Create user source -->
  <div v-else>
    <h2 class="box__title">
      {{ $t('userSourceSettings.titleAddUserSource') }}
    </h2>
    <Error :error="error"></Error>
    <CreateUserSourceForm
      ref="userSourceForm"
      :builder="builder"
      :integrations="integrations"
      @submitted="createUserSource"
      @values-changed="onValueChange"
    />
    <div class="actions">
      <Button
        type="link"
        prepend-icon="iconoir-nav-arrow-left"
        @click="hideForm"
      >
        {{ $t('action.back') }}
      </Button>
      <Button
        :disabled="actionInProgress || invalidForm"
        :loading="actionInProgress"
        size="large"
        @click="$refs.userSourceForm.submit()"
      >
        {{ $t('action.create') }}
      </Button>
    </div>
  </div>
</template>

<script>
import { mapActions, mapGetters } from 'vuex'
import error from '@baserow/modules/core/mixins/error'
import { clone } from '@baserow/modules/core/utils/object'
import { notifyIf } from '@baserow/modules/core/utils/error'
import CreateUserSourceForm from '@baserow/modules/builder/components/userSource/CreateUserSourceForm'
import UpdateUserSourceForm from '@baserow/modules/builder/components/userSource/UpdateUserSourceForm'

export default {
  name: 'UserSourceSettings',
  components: { CreateUserSourceForm, UpdateUserSourceForm },
  mixins: [error],
  props: {
    builder: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      showCreateForm: false,
      editedUserSource: null,
      actionInProgress: false,
      invalidForm: false,
    }
  },
  async fetch() {
    try {
      await this.actionFetchIntegrations({ applicationId: this.builder.id })
      await this.actionFetchUserSources({ applicationId: this.builder.id })
      this.hideError()
    } catch (error) {
      this.handleError(error)
    }
  },
  computed: {
    ...mapGetters({
      userSources: 'userSource/getUserSources',
      integrations: 'integration/getIntegrations',
    }),
    userSourceTypes() {
      return this.$registry.getAll('userSource')
    },
  },
  methods: {
    ...mapActions({
      actionFetchIntegrations: 'integration/fetch',
      actionFetchUserSources: 'userSource/fetch',
      actionCreateUserSource: 'userSource/create',
      actionUpdateUserSource: 'userSource/update',
      actionDeleteUserSource: 'userSource/delete',
    }),
    getUserSourceType(userSource) {
      return this.$registry.get('userSource', userSource.type)
    },
    onValueChange() {
      this.invalidForm = !this.$refs.userSourceForm.isFormValid()
    },
    async showForm(userSourceToEdit) {
      if (userSourceToEdit) {
        this.editedUserSource = userSourceToEdit
      } else {
        this.showCreateForm = true
      }
      await this.$nextTick()
      this.onValueChange()
    },
    hideForm() {
      this.showCreateForm = false
      this.editedUserSource = null
      this.hideError()
      this.invalidForm = false
    },
    async createUserSource(values) {
      this.actionInProgress = true
      const { type, ...rest } = values
      try {
        const createdUserSource = await this.actionCreateUserSource({
          applicationId: this.builder.id,
          userSourceType: type,
          values: rest,
        })

        this.hideForm()
        // immediately select this user source to edit it.
        this.editedUserSource = createdUserSource
      } catch (error) {
        this.handleError(error)
      }
      this.actionInProgress = false
    },
    async updateUserSource(newValues) {
      this.actionInProgress = true
      try {
        await this.actionUpdateUserSource({
          page: this.page,
          userSourceId: this.editedUserSource.id,
          values: clone(newValues),
        })
        this.hideForm()
      } catch (error) {
        // Restore the previously saved values from the store
        this.$refs.userSourceForm.reset()
        this.handleError(error)
      }
      this.actionInProgress = false
    },
    async deleteUserSource(userSource) {
      try {
        await this.actionDeleteUserSource({ userSourceId: userSource.id })
      } catch (error) {
        notifyIf(error)
      }
    },
  },
}
</script>
