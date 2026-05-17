export type ToolHandler = (params: Record<string, any>) => any;

export class Router {
  private registeredTools: string[];
  private mcpServers: Record<string, any>;
  private handlers: Map<string, ToolHandler>;

  constructor(tools: string[], mcpServers: Record<string, any>) {
    this.registeredTools = tools;
    this.mcpServers = mcpServers;
    this.handlers = new Map();
  }

  public registerTool(name: string, handler: ToolHandler): void {
    this.handlers.set(name, handler);
  }

  public route(toolName: string, params: Record<string, any>): any {
    const handler = this.handlers.get(toolName);
    if (handler) {
      return handler(params);
    }
    
    // In a full implementation, this would route to an MCP client
    // For now, it throws if not handled.
    throw new Error(`Tool not found or not registered: ${toolName}`);
  }
}
