export function LoadingState({ children = 'Loading heroes…' }: { children?: string }) { return <p className="state" role="status">{children}</p> }
export function EmptyState() { return <p className="state">No heroes match those filters.</p> }
export function ErrorState({ message, retry }: { message: string; retry: () => void }) { return <div className="state" role="alert"><p>{message}</p><button onClick={retry}>Try again</button></div> }
