export function navigate(path: string) {
  history.pushState({}, '', path)
  dispatchEvent(new PopStateEvent('popstate'))
}
