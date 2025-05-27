import React, { useState, useEffect } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { KnowledgeAlgorithm } from '@/types/simulation';
import { 
  Plus, 
  // Trash2, 
  Settings, 
  Play, 
  Pause, 
  RefreshCw, 
  Package, 
  Zap,
  Code2,
  AlertCircle,
  CheckCircle
} from 'lucide-react';
import { pluginAPI } from '@/lib/api-client';
import { toast } from 'sonner';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
// Note: Switch removed as it's not currently used
// import { formatTimestamp } from '@/lib/utils'; // Not used in current implementation

interface PluginPanelProps {
  plugins: KnowledgeAlgorithm[];
  sessionId: string;
  onPluginsChange?: () => void;
}

export function PluginPanel({ plugins: propPlugins, sessionId, onPluginsChange }: PluginPanelProps) {
  const [plugins, setPlugins] = useState<KnowledgeAlgorithm[]>(propPlugins || []);
  const [isLoading, setIsLoading] = useState(false);
  const [isReloading, setIsReloading] = useState(false);
  const [runningTests, setRunningTests] = useState<Set<string>>(new Set());
  const [testResults, setTestResults] = useState<Record<string, any>>({});
  
  // New plugin dialog state
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [newPluginName, setNewPluginName] = useState('');
  const [newPluginDescription, setNewPluginDescription] = useState('');
  const [newPluginType, setNewPluginType] = useState('KA');

  // Load plugins on mount and when sessionId changes
  useEffect(() => {
    loadPlugins();
  }, [sessionId]);

  // Update local state when prop changes
  useEffect(() => {
    if (propPlugins) {
      setPlugins(propPlugins);
    }
  }, [propPlugins]);

  const loadPlugins = async () => {
    try {
      setIsLoading(true);
      const fetchedPlugins = await pluginAPI.listKAs();
      console.log('Loaded plugins:', fetchedPlugins);
      
      // Transform API response to match our KnowledgeAlgorithm interface
      const transformedPlugins: KnowledgeAlgorithm[] = fetchedPlugins.map((plugin: any, index: number) => ({
        id: plugin.name || `plugin-${index}`,
        name: plugin.name || `Unknown Plugin ${index}`,
        description: plugin.meta?.description || 'No description available',
        version: plugin.meta?.version || '1.0.0',
        active: plugin.meta?.active !== false, // Default to true if not specified
        type: plugin.meta?.type || 'KA',
        params: plugin.meta?.params || {},
        layers: plugin.meta?.layers || [1, 2, 3], // Default layers
        metadata: plugin.meta || {}
      }));
      
      setPlugins(transformedPlugins);
      onPluginsChange?.();
    } catch (error) {
      console.error('Failed to load plugins:', error);
      toast.error("Failed to load plugins", {
        description: error instanceof Error ? error.message : "Unknown error",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleReloadPlugins = async () => {
    try {
      setIsReloading(true);
      const result = await pluginAPI.reloadKAs();
      console.log('Plugins reloaded:', result);
      
      toast.success("Plugins reloaded successfully", {
        description: `${result.available?.length || 0} plugins available`,
      });
      
      // Reload the plugin list
      await loadPlugins();
    } catch (error) {
      console.error('Failed to reload plugins:', error);
      toast.error("Failed to reload plugins", {
        description: error instanceof Error ? error.message : "Unknown error occurred",
      });
    } finally {
      setIsReloading(false);
    }
  };

  const handleTogglePlugin = async (plugin: KnowledgeAlgorithm) => {
    try {
      const newStatus = !plugin.active;
      
      // Update local state optimistically
      setPlugins(prev => prev.map(p => 
        p.id === plugin.id ? { ...p, active: newStatus } : p
      ));
      
      toast.success(`Plugin ${newStatus ? 'activated' : 'deactivated'}`, {
        description: `${plugin.name} is now ${newStatus ? 'active' : 'inactive'}`,
      });
      
      onPluginsChange?.();
    } catch (error) {
      console.error('Failed to toggle plugin:', error);
      toast.error("Failed to toggle plugin", {
        description: error instanceof Error ? error.message : "Unknown error occurred",
      });
      
      // Revert optimistic update on error
      await loadPlugins();
    }
  };

  const handleTestPlugin = async (plugin: KnowledgeAlgorithm) => {
    try {
      setRunningTests(prev => new Set(prev).add(plugin.id));
      
      const testPayload = {
        query: `Test query for ${plugin.name}`,
        test_mode: true,
        timestamp: new Date().toISOString()
      };
      
      console.log(`Testing plugin ${plugin.name} with payload:`, testPayload);
      const result = await pluginAPI.runKA(plugin.name, testPayload);
      
      setTestResults(prev => ({
        ...prev,
        [plugin.id]: {
          success: true,
          result,
          timestamp: new Date().toISOString()
        }
      }));
      
      toast.success("Plugin test completed", {
        description: `${plugin.name} executed successfully`,
      });
    } catch (error) {
      console.error(`Failed to test plugin ${plugin.name}:`, error);
      
      setTestResults(prev => ({
        ...prev,
        [plugin.id]: {
          success: false,
          error: error instanceof Error ? error.message : "Unknown error",
          timestamp: new Date().toISOString()
        }
      }));
      
      toast.error("Plugin test failed", {
        description: `${plugin.name}: ${error instanceof Error ? error.message : "Unknown error"}`,
      });
    } finally {
      setRunningTests(prev => {
        const newSet = new Set(prev);
        newSet.delete(plugin.id);
        return newSet;
      });
    }
  };

  const handleAddPlugin = async () => {
    if (!newPluginName.trim()) {
      toast.error("Missing required field", {
        description: "Plugin name is required",
      });
      return;
    }

    try {
      // For now, just add to local state as the backend plugin system 
      // handles file-based plugins
      const newPlugin: KnowledgeAlgorithm = {
        id: `custom-${Date.now()}`,
        name: newPluginName.trim(),
        description: newPluginDescription.trim() || 'Custom plugin',
        version: '1.0.0',
        active: true,
        type: newPluginType,
        params: {},
        layers: [1, 2, 3],
        metadata: {
          custom: true,
          created_at: new Date().toISOString()
        }
      };

      setPlugins(prev => [...prev, newPlugin]);
      
      toast.success("Plugin configuration added", {
        description: "Plugin will be available after backend reload",
      });
      
      // Reset form
      setNewPluginName('');
      setNewPluginDescription('');
      setNewPluginType('KA');
      setIsAddDialogOpen(false);
      
      onPluginsChange?.();
    } catch (error) {
      console.error('Failed to add plugin:', error);
      toast.error("Failed to add plugin", {
        description: error instanceof Error ? error.message : "Unknown error occurred",
      });
    }
  };

  const activePlugins = plugins.filter(p => p.active);
  const inactivePlugins = plugins.filter(p => !p.active);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-sm text-gray-600">Loading plugins...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Package className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold">Knowledge Algorithm Plugins</h3>
          <Badge variant="outline" className="ml-2">
            {activePlugins.length} active
          </Badge>
        </div>
        
        <div className="flex gap-2">
          <Button 
            size="sm" 
            variant="outline"
            onClick={handleReloadPlugins}
            disabled={isReloading}
            className="flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${isReloading ? 'animate-spin' : ''}`} />
            Reload
          </Button>
          
          <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
            <DialogTrigger asChild>
              <Button size="sm" className="flex items-center gap-2">
                <Plus className="w-4 h-4" />
                Add Plugin
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <Code2 className="w-5 h-5" />
                  Add Knowledge Algorithm Plugin
                </DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="plugin-name">Plugin Name *</Label>
                  <Input
                    id="plugin-name"
                    value={newPluginName}
                    onChange={(e) => setNewPluginName(e.target.value)}
                    placeholder="e.g., advanced_reasoning_ka"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="plugin-description">Description</Label>
                  <Textarea
                    id="plugin-description"
                    value={newPluginDescription}
                    onChange={(e) => setNewPluginDescription(e.target.value)}
                    placeholder="Brief description of the plugin's capabilities"
                    rows={3}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="plugin-type">Type</Label>
                  <Input
                    id="plugin-type"
                    value={newPluginType}
                    onChange={(e) => setNewPluginType(e.target.value)}
                    placeholder="KA, Processor, Analyzer, etc."
                  />
                </div>
                <Button 
                  className="w-full" 
                  onClick={handleAddPlugin}
                  disabled={!newPluginName.trim()}
                >
                  Add Plugin Configuration
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Active Plugins */}
      <div className="space-y-3">
        <h4 className="font-medium text-sm text-gray-700 uppercase tracking-wide">
          Active Plugins ({activePlugins.length})
        </h4>
        
        {activePlugins.length === 0 ? (
          <div className="text-center py-8 text-gray-500 border-2 border-dashed border-gray-300 rounded-lg">
            <Package className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No active plugins</p>
            <p className="text-xs">Add or activate plugins to enhance simulation capabilities</p>
          </div>
        ) : (
          <div className="space-y-2">
            {activePlugins.map(plugin => {
              const testResult = testResults[plugin.id];
              const isTestRunning = runningTests.has(plugin.id);
              
              return (
                <div key={plugin.id} className="flex items-center justify-between p-4 border rounded-lg bg-white hover:bg-gray-50 transition-colors">
                  <div className="flex items-center gap-3 flex-1">
                    <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h5 className="font-semibold text-sm truncate">{plugin.name}</h5>
                        <Badge variant="secondary" className="text-xs">
                          {plugin.type}
                        </Badge>
                        <Badge variant="outline" className="text-xs">
                          v{plugin.version}
                        </Badge>
                      </div>
                      <p className="text-xs text-gray-600 mb-1 truncate">
                        {plugin.description}
                      </p>
                      <div className="flex items-center gap-4 text-xs text-gray-500">
                        <span>Layers: {plugin.layers.join(', ')}</span>
                        {testResult && (
                          <span className={`flex items-center gap-1 ${testResult.success ? 'text-green-600' : 'text-red-600'}`}>
                            {testResult.success ? (
                              <CheckCircle className="w-3 h-3" />
                            ) : (
                              <AlertCircle className="w-3 h-3" />
                            )}
                            Last test: {testResult.success ? 'Passed' : 'Failed'}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex gap-1 ml-4">
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => handleTestPlugin(plugin)}
                      disabled={isTestRunning}
                      title="Test Plugin"
                    >
                      {isTestRunning ? (
                        <div className="w-3 h-3 animate-spin rounded-full border border-blue-600 border-t-transparent" />
                      ) : (
                        <Play className="w-3 h-3" />
                      )}
                    </Button>
                    <Button size="sm" variant="outline" title="Plugin Settings">
                      <Settings className="w-3 h-3" />
                    </Button>
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => handleTogglePlugin(plugin)}
                      title="Deactivate Plugin"
                      className="text-yellow-600 hover:text-yellow-700 hover:bg-yellow-50"
                    >
                      <Pause className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Inactive Plugins */}
      {inactivePlugins.length > 0 && (
        <div className="space-y-3">
          <h4 className="font-medium text-sm text-gray-700 uppercase tracking-wide">
            Inactive Plugins ({inactivePlugins.length})
          </h4>
          <div className="space-y-2">
            {inactivePlugins.map(plugin => (
              <div key={plugin.id} className="flex items-center justify-between p-4 border rounded-lg bg-gray-50 opacity-75">
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 bg-gray-400 rounded-full"></div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h5 className="font-medium text-sm text-gray-700">{plugin.name}</h5>
                      <Badge variant="outline" className="text-xs">
                        {plugin.type}
                      </Badge>
                    </div>
                    <p className="text-xs text-gray-500 truncate">
                      {plugin.description}
                    </p>
                  </div>
                </div>
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={() => handleTogglePlugin(plugin)}
                  title="Activate Plugin"
                  className="text-green-600 hover:text-green-700 hover:bg-green-50"
                >
                  <Zap className="w-3 h-3" />
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Plugin Statistics */}
      <div className="grid grid-cols-3 gap-4 pt-4 border-t">
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">{activePlugins.length}</div>
          <div className="text-xs text-gray-500">Active</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-600">{inactivePlugins.length}</div>
          <div className="text-xs text-gray-500">Inactive</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-600">{plugins.length}</div>
          <div className="text-xs text-gray-500">Total</div>
        </div>
      </div>
    </div>
  );
}