// UI data only, not API response types. Future integration maps real data into these props.
// No example projects, requests, endpoints, or simulated network delays live here.
export type ResourceState<T> =
  | { status: 'empty' }
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; data: T }

export type ProjectView = {
  id: string
  name: string
  description?: string
  documentCount?: number
}
