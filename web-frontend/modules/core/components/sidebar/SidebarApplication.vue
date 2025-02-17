<template>
  <li
    class="tree__item"
    :class="{
      active: application._.selected,
      'tree__item--loading': application._.loading,
    }"
  >
    <div class="tree__action tree__action--has-options" data-sortable-handle>
      <a
        class="tree__link"
        :title="application.name"
        @click="$emit('selected', application)"
      >
        <i
          class="tree__icon tree__icon--type"
          :class="application._.type.iconClass"
        ></i>
        <span class="tree__link-text">
          <Editable
            ref="rename"
            :value="application.name"
            @change="renameApplication(application, $event)"
          ></Editable>
        </span>
      </a>

      <a
        ref="contextLink"
        class="tree__options"
        @click="$refs.context.toggle($refs.contextLink, 'bottom', 'right', 0)"
        @mousedown.stop
      >
        <i class="baserow-icon-more-vertical"></i>
      </a>

      <Context
        ref="context"
        :overflow-scroll="true"
        :max-height-if-outside-viewport="true"
      >
        <div class="context__menu-title">
          {{ application.name }} ({{ application.id }})
        </div>
        <ul class="context__menu">
          <li
            v-for="(component, index) in additionalContextComponents"
            :key="index"
            class="context__menu-item"
            @click="$refs.context.hide()"
          >
            <component :is="component" :application="application"></component>
          </li>
          <slot name="context"></slot>
          <li
            v-if="
              $hasPermission(
                'application.update',
                application,
                application.workspace.id
              )
            "
            class="context__menu-item"
          >
            <a class="context__menu-item-link" @click="enableRename()">
              <i class="context__menu-item-icon iconoir-edit-pencil"></i>
              {{
                $t('sidebarApplication.rename', {
                  type: application._.type.name.toLowerCase(),
                })
              }}
            </a>
          </li>
          <li
            v-if="
              $hasPermission(
                'application.duplicate',
                application,
                application.workspace.id
              )
            "
            class="context__menu-item"
          >
            <SidebarDuplicateApplicationContextItem
              :application="application"
              :disabled="deleting"
              @click="$refs.context.hide()"
            ></SidebarDuplicateApplicationContextItem>
          </li>
          <li
            v-if="
              $hasPermission(
                'application.create_snapshot',
                application,
                application.workspace.id
              )
            "
            class="context__menu-item"
          >
            <a class="context__menu-item-link" @click="openSnapshots">
              <i class="context__menu-item-icon baserow-icon-history"></i>
              {{ $t('sidebarApplication.snapshots') }}
            </a>
          </li>
          <SnapshotsModal
            ref="snapshotsModal"
            :application="application"
          ></SnapshotsModal>
          <li
            v-if="
              $hasPermission(
                'application.read_trash',
                application,
                application.workspace.id
              )
            "
            class="context__menu-item"
          >
            <a
              class="context__menu-item-link"
              @click="showApplicationTrashModal"
            >
              <i class="context__menu-item-icon iconoir-refresh-double"></i>
              {{ $t('sidebarApplication.viewTrash') }}
            </a>
          </li>
          <li
            v-if="
              $hasPermission(
                'application.delete',
                application,
                application.workspace.id
              )
            "
            class="context__menu-item context__menu-item--with-separator"
          >
            <a
              class="context__menu-item-link context__menu-item-link--delete"
              :class="{ 'context__menu-item-link--loading': deleting }"
              @click="deleteApplication()"
            >
              <i class="context__menu-item-icon iconoir-bin"></i>
              {{
                $t('sidebarApplication.delete', {
                  type: application._.type.name.toLowerCase(),
                })
              }}
            </a>
          </li>
        </ul>
      </Context>
      <TrashModal
        ref="applicationTrashModal"
        :initial-workspace="workspace"
        :initial-application="application"
      >
      </TrashModal>
    </div>
    <slot name="body"></slot>
  </li>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import SidebarDuplicateApplicationContextItem from '@baserow/modules/core/components/sidebar/SidebarDuplicateApplicationContextItem.vue'
import TrashModal from '@baserow/modules/core/components/trash/TrashModal'
import SnapshotsModal from '@baserow/modules/core/components/snapshots/SnapshotsModal'

export default {
  name: 'SidebarApplication',
  components: {
    TrashModal,
    SidebarDuplicateApplicationContextItem,
    SnapshotsModal,
  },
  props: {
    application: {
      type: Object,
      required: true,
    },
    workspace: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      deleting: false,
    }
  },
  computed: {
    additionalContextComponents() {
      return Object.values(this.$registry.getAll('plugin'))
        .reduce(
          (components, plugin) =>
            components.concat(
              plugin.getAdditionalDatabaseContextComponents(
                this.workspace,
                this.application
              )
            ),
          []
        )
        .filter((component) => component !== null)
    },
  },
  methods: {
    setLoading(application, value) {
      this.$store.dispatch('application/setItemLoading', {
        application,
        value,
      })
    },
    enableRename() {
      this.$refs.context.hide()
      this.$refs.rename.edit()
    },
    async renameApplication(application, event) {
      this.setLoading(application, true)

      try {
        await this.$store.dispatch('application/update', {
          application,
          values: {
            name: event.value,
          },
        })
      } catch (error) {
        this.$refs.rename.set(event.oldValue)
        notifyIf(error, 'application')
      }

      this.setLoading(application, false)
    },
    async deleteApplication() {
      if (this.deleting) {
        return
      }

      this.deleting = true

      try {
        await this.$store.dispatch('application/delete', this.application)
        await this.$store.dispatch('toast/restore', {
          trash_item_type: 'application',
          trash_item_id: this.application.id,
        })
      } catch (error) {
        notifyIf(error, 'application')
      }

      this.deleting = false
    },
    showApplicationTrashModal() {
      this.$refs.context.hide()
      this.$refs.applicationTrashModal.show()
    },
    openSnapshots() {
      this.$refs.context.hide()
      this.$refs.snapshotsModal.show()
    },
  },
}
</script>
