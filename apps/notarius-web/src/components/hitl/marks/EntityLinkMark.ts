/**
 * TipTap Mark extension for entity links
 * Renders spans with entity ID and subtle background
 */

import { Mark, mergeAttributes } from '@tiptap/core';

export interface EntityLinkOptions {
  HTMLAttributes: Record<string, any>;
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    entityLink: {
      /**
       * Set an entity link mark
       */
      setEntityLink: (attributes: { entityId: string }) => ReturnType;
      /**
       * Toggle an entity link mark
       */
      toggleEntityLink: (attributes: { entityId: string }) => ReturnType;
      /**
       * Unset an entity link mark
       */
      unsetEntityLink: () => ReturnType;
    };
  }
}

export const EntityLinkMark = Mark.create<EntityLinkOptions>({
  name: 'entityLink',

  addOptions() {
    return {
      HTMLAttributes: {},
    };
  },

  addAttributes() {
    return {
      entityId: {
        default: null,
        parseHTML: (element) => element.getAttribute('data-entity-id'),
        renderHTML: (attributes) => {
          if (!attributes.entityId) {
            return {};
          }
          return {
            'data-entity-id': attributes.entityId,
          };
        },
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'span[data-entity-id]',
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      'span',
      mergeAttributes(this.options.HTMLAttributes, HTMLAttributes, {
        class: 'entity-link bg-blue-50 border-b border-blue-200 px-0.5 rounded',
      }),
      0,
    ];
  },

  addCommands() {
    return {
      setEntityLink:
        (attributes) =>
        ({ commands }) => {
          return commands.setMark(this.name, attributes);
        },
      toggleEntityLink:
        (attributes) =>
        ({ commands }) => {
          return commands.toggleMark(this.name, attributes);
        },
      unsetEntityLink:
        () =>
        ({ commands }) => {
          return commands.unsetMark(this.name);
        },
    };
  },
});


