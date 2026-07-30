export const colors = {
  node: {
    default: 'gold',
    darken: 'grey',
    select: 'green',
    neighbor: '#00ff00',
    oldest: '#ff0000',
    outComponent: 'orange',
    temporalDefault: "white",
  },
  edge: {
    default: 'ivory',
    darken: 'grey',
    select: '#111111',
    outComponent: 'blue',
  },
  background: {
    default: '#ffffff',
    muted: '#f5f5f5',
  },
} as const

export const sizes = {
    node: {
        default: 3,
        selected: 4,
        temporalDefault: 10,
    },
    edge: {
        default: 1,
        decreased: 0.5,
    }
}

export type Colors = typeof colors
export type Sizes = typeof sizes