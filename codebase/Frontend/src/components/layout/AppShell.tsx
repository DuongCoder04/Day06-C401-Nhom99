type AppShellProps = {
  left: React.ReactNode
  center: React.ReactNode
  right: React.ReactNode
}

export function AppShell({ left, center, right }: AppShellProps) {
  return (
    <main className="app-shell">
      <aside className="panel panel-left">{left}</aside>
      <section className="panel panel-center">{center}</section>
      <aside className="panel panel-right">{right}</aside>
    </main>
  )
}
