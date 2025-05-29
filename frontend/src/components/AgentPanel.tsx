import React, { useState, useEffect, useCallback } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Agent } from '@/types/simulation';
import { Plus, Trash2, Settings, Activity, User } from 'lucide-react';
import { agentAPI } from '@/lib/api-client';
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
import { formatTimestamp } from '@/lib/utils';

interface AgentPanelProps {
  agents: Agent[];
  sessionId: string;
  onAgentsChange?: () => void;
}

export function AgentPanel({ agents: propAgents, sessionId, onAgentsChange }: AgentPanelProps) {
  const [agents, setAgents] = useState<Agent[]>(propAgents || []);
  const [isSpawning, setIsSpawning] = useState(false);
  const [isTerminating, setIsTerminating] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [newAgentName, setNewAgentName] = useState('');
  const [newAgentRole, setNewAgentRole] = useState('');
  const [newAgentPersona, setNewAgentPersona] = useState('');
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const loadAgents = useCallback(async () => {
    try {
      setIsLoading(true);
      const fetchedAgents = await agentAPI.list();
      setAgents(fetchedAgents);
      onAgentsChange?.();
    } catch (error) {
      console.error('Failed to load agents:', error);
      toast.error("Failed to load agents", {
        description: error instanceof Error ? error.message : "Unknown error",
      });
    } finally {
      setIsLoading(false);
    }
  }, [onAgentsChange]);

  useEffect(() => {
    loadAgents();
  }, [sessionId, loadAgents]);

  // Update local state when prop changes
  useEffect(() => {
    if (propAgents) {
      setAgents(propAgents);
    }
  }, [propAgents]);

  const handleSpawnAgent = async () => {
    if (!newAgentName.trim() || !newAgentRole.trim()) {
      toast.error("Missing required fields", {
        description: "Name and role are required to spawn an agent",
      });
      return;
    }

    try {
      setIsSpawning(true);
      
      const request = {
        name: newAgentName.trim(),
        role: newAgentRole.trim(),
        persona: newAgentPersona.trim() || 'default',
      };

      console.log('Spawning agent with request:', request);
      const newAgent = await agentAPI.spawn(request);
      console.log('Agent spawned:', newAgent);
      
      toast.success("Agent spawned successfully", {
        description: `${newAgent.name} (${newAgent.role}) is now active`,
      });
      
      // Reset form
      setNewAgentName('');
      setNewAgentRole('');
      setNewAgentPersona('');
      setIsDialogOpen(false);
      
      // Reload agents to get updated list
      await loadAgents();
      
    } catch (error) {
      console.error('Failed to spawn agent:', error);
      toast.error("Failed to spawn agent", {
        description: error instanceof Error ? error.message : "Unknown error occurred",
      });
    } finally {
      setIsSpawning(false);
    }
  };

  const handleTerminateAgent = async (agentId: string, agentName: string) => {
    try {
      setIsTerminating(agentId);
      console.log('Terminating agent:', agentId);
      
      const result = await agentAPI.kill(agentId);
      console.log('Agent terminated:', result);
      
      toast.success("Agent terminated", {
        description: `${agentName} has been deactivated`,
      });
      
      // Reload agents to get updated list
      await loadAgents();
      
    } catch (error) {
      console.error('Failed to terminate agent:', error);
      toast.error("Failed to terminate agent", {
        description: error instanceof Error ? error.message : "Unknown error occurred",
      });
    } finally {
      setIsTerminating(null);
    }
  };

  const activeAgents = agents.filter(a => a.active);
  const inactiveAgents = agents.filter(a => !a.active);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-sm text-gray-600">Loading agents...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with spawn button */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold">Agent Management</h3>
          <Badge variant="outline" className="ml-2">
            {activeAgents.length} active
          </Badge>
        </div>
        
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button size="sm" className="flex items-center gap-2">
              <Plus className="w-4 h-4" />
              Spawn Agent
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <User className="w-5 h-5" />
                Spawn New Agent
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Agent Name *</Label>
                <Input
                  id="name"
                  value={newAgentName}
                  onChange={(e) => setNewAgentName(e.target.value)}
                  placeholder="e.g., Research Assistant Alpha"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="role">Role *</Label>
                <Input
                  id="role"
                  value={newAgentRole}
                  onChange={(e) => setNewAgentRole(e.target.value)}
                  placeholder="e.g., RESEARCHER, ANALYST, CRITIC"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="persona">Persona</Label>
                <Input
                  id="persona"
                  value={newAgentPersona}
                  onChange={(e) => setNewAgentPersona(e.target.value)}
                  placeholder="e.g., domain_expert, skeptic (optional)"
                />
              </div>
              <Button 
                className="w-full" 
                onClick={handleSpawnAgent}
                disabled={isSpawning || !newAgentName.trim() || !newAgentRole.trim()}
              >
                {isSpawning ? "Spawning..." : "Spawn Agent"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Active Agents */}
      <div className="space-y-3">
        <h4 className="font-medium text-sm text-gray-700 uppercase tracking-wide">
          Active Agents ({activeAgents.length})
        </h4>
        
        {activeAgents.length === 0 ? (
          <div className="text-center py-8 text-gray-500 border-2 border-dashed border-gray-300 rounded-lg">
            <User className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No active agents</p>
            <p className="text-xs">Spawn an agent to get started</p>
          </div>
        ) : (
          <div className="space-y-2">
            {activeAgents.map(agent => (
              <div key={agent.id} className="flex items-center justify-between p-4 border rounded-lg bg-white hover:bg-gray-50 transition-colors">
                <div className="flex items-center gap-3 flex-1">
                  <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h5 className="font-semibold text-sm truncate">{agent.name}</h5>
                      <Badge variant="secondary" className="text-xs">
                        {agent.role}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      {agent.persona && agent.persona !== 'default' && (
                        <span className="flex items-center gap-1">
                          <User className="w-3 h-3" />
                          {agent.persona}
                        </span>
                      )}
                      <span>
                        Created: {formatTimestamp(agent.created_at)}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className="flex gap-1 ml-4">
                  <Button size="sm" variant="outline" title="Agent Settings">
                    <Settings className="w-3 h-3" />
                  </Button>
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => handleTerminateAgent(agent.id, agent.name)}
                    disabled={isTerminating === agent.id}
                    title="Terminate Agent"
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    {isTerminating === agent.id ? (
                      <div className="w-3 h-3 animate-spin rounded-full border border-red-600 border-t-transparent" />
                    ) : (
                      <Trash2 className="w-3 h-3" />
                    )}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Inactive Agents */}
      {inactiveAgents.length > 0 && (
        <div className="space-y-3">
          <h4 className="font-medium text-sm text-gray-700 uppercase tracking-wide">
            Inactive Agents ({inactiveAgents.length})
          </h4>
          <div className="space-y-2">
            {inactiveAgents.map(agent => (
              <div key={agent.id} className="flex items-center justify-between p-4 border rounded-lg bg-gray-50 opacity-75">
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 bg-gray-400 rounded-full"></div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h5 className="font-medium text-sm text-gray-700">{agent.name}</h5>
                      <Badge variant="outline" className="text-xs">
                        {agent.role}
                      </Badge>
                    </div>
                    <p className="text-xs text-gray-500">
                      Terminated • Created: {formatTimestamp(agent.created_at)}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Agent Statistics */}
      <div className="grid grid-cols-3 gap-4 pt-4 border-t">
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">{activeAgents.length}</div>
          <div className="text-xs text-gray-500">Active</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-600">{inactiveAgents.length}</div>
          <div className="text-xs text-gray-500">Inactive</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-600">{agents.length}</div>
          <div className="text-xs text-gray-500">Total</div>
        </div>
      </div>
    </div>
  );
}
