<template>
  <form>
    <FormGroup
      :label="$t('createUserSourceForm.userSourceType')"
      :error="getError('type')"
    >
      <Dropdown
        v-model="$v.values.type.$model"
        :show-search="false"
        class="user-source-settings__user-source-type"
      >
        <DropdownItem
          v-for="userSourceType in userSourceTypes"
          :key="userSourceType.type"
          :name="userSourceType.name"
          :value="userSourceType.type"
          :image="userSourceType.integrationType.image"
        />
      </Dropdown>
    </FormGroup>
    <FormGroup
      :label="$t('createUserSourceForm.userSourceIntegration')"
      :error="getError('integration_id')"
    >
      <IntegrationDropdown
        v-model="$v.values.integration_id.$model"
        :application="builder"
        :integrations="integrations"
        :integration-type="currentUserSourceType?.integrationType"
      />
    </FormGroup>
    <FormInput
      v-model="$v.values.name.$model"
      :error="getError('name')"
      :label="$t('createUserSourceForm.userSourceName')"
    />
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import IntegrationDropdown from '@baserow/modules/core/components/integrations/IntegrationDropdown'
import { required, maxLength } from 'vuelidate/lib/validators'
import { getNextAvailableNameInSequence } from '@baserow/modules/core/utils/string'
import { mapGetters } from 'vuex'

export default {
  name: 'CreateUserSourceForm',
  components: { IntegrationDropdown },
  mixins: [form],
  props: {
    builder: {
      type: Object,
      required: true,
    },
    integrations: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      values: { type: null, name: '', integration_id: null },
    }
  },
  computed: {
    ...mapGetters({
      userSources: 'userSource/getUserSources',
    }),
    userSourceTypes() {
      return Object.values(this.$registry.getOrderedList('userSource'))
    },
    currentUserSourceType() {
      if (!this.values.type) {
        return null
      } else {
        return this.$registry.get('userSource', this.values.type)
      }
    },
    userSourceNames() {
      return this.userSources.map(({ name }) => name)
    },
  },
  watch: {
    currentUserSourceType(newValue) {
      this.values.name = getNextAvailableNameInSequence(
        newValue.name,
        this.userSourceNames
      )
    },
  },
  methods: {
    getError(fieldName) {
      if (!this.$v.values[fieldName].$dirty) {
        return ''
      }
      const fieldState = this.$v.values[fieldName]
      if (!fieldState.required) {
        return this.$t('error.requiredField')
      }
      if (fieldName === 'name' && !fieldState.maxLength) {
        return this.$t('error.maxLength', { max: 255 })
      }
      return ''
    },
  },
  validations: {
    values: {
      type: {
        required,
      },
      integration_id: {
        required,
      },
      name: {
        required,
        maxLength: maxLength(255),
      },
    },
  },
}
</script>
