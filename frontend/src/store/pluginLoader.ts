// Plugin/KA Loading System
// This allows dynamic registration and loading of plugin modules or Knowledge Assets (KA).

export type Plugin = {
    id: string;
    name: string;
    init: () => void;
  };
  
  class PluginLoader {
    private plugins: Map<string, Plugin> = new Map();
  
    registerPlugin(plugin: Plugin) {
      this.plugins.set(plugin.id, plugin);
      plugin.init();
    }
  
    getPlugin(id: string): Plugin | undefined {
      return this.plugins.get(id);
    }
  
    listPlugins(): Plugin[] {
      return Array.from(this.plugins.values());
    }
  }
  
  export const pluginLoader = new PluginLoader();
  