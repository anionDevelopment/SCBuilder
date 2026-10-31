// Reports the state of opencode to scrais (see the article "RunAgentInSandbox" of ScriptCollection).
export const ScraisAgentStatus = async ({ $ }) => {
  const report = (token) => $`/usr/local/bin/scrais-agent-status ${token}`.quiet().nothrow();
  // A subagent runs in an own session whose end does not mean that opencode waits for input.
  const subagentSessions = new Set();

  return {
    event: async ({ event }) => {
      const properties = event.properties ?? {};
      switch (event.type) {
        case "session.created":
          if (properties.info?.parentID) {
            subagentSessions.add(properties.info.id);
          }
          break;
        case "session.status":
          if (!subagentSessions.has(properties.sessionID)) {
            await report(properties.status?.type === "idle" ? "idle" : "working");
          }
          break;
        case "permission.asked":
          await report("blocked");
          break;
        case "permission.replied":
          await report("working");
          break;
      }
    },
  };
};
