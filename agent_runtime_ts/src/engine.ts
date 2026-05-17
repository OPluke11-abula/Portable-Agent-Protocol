import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'yaml';
import { Router } from './router';

const FRONTMATTER_RE = /^---\s*\n(.*?)\n---\s*\n/s;

export interface AgentConfig {
  protocol_version?: string;
  name?: string;
  version?: string;
  tools?: string[];
  mcp_servers?: Record<string, any>;
  [key: string]: any;
}

export class AgentEngine {
  public configPath: string;
  public config: AgentConfig;
  public router: Router;

  constructor(configPath: string = '.agent/agent.md') {
    this.configPath = path.resolve(configPath);
    this.config = this.loadConfig(this.configPath);
    this.router = new Router(this.config.tools || [], this.config.mcp_servers || {});
    
    console.log(`[AgentEngine] Initialised - name=${this.config.name} version=${this.config.version}`);
  }

  private loadConfig(filePath: string): AgentConfig {
    if (!fs.existsSync(filePath)) {
      throw new Error(`Config file not found: ${filePath}`);
    }

    const text = fs.readFileSync(filePath, 'utf-8');
    const match = FRONTMATTER_RE.exec(text);
    
    if (!match) {
      throw new Error(`No YAML front matter found in ${filePath}`);
    }

    try {
      return yaml.parse(match[1]) as AgentConfig;
    } catch (err) {
      throw new Error(`Failed to parse YAML front matter: ${err}`);
    }
  }

  public run(tool: string, params: Record<string, any> = {}): any {
    console.log(`[AgentEngine] Dispatching - tool=${tool} params=${JSON.stringify(params)}`);
    return this.router.route(tool, params);
  }
}
