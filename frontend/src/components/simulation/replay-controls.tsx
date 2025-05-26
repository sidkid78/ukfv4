'use client';

import React from 'react';
import { useSimulationStore } from '@/state/useSimulationStore';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Card, CardContent } from '@/components/ui/card';
import { 
  SkipBack, 
  StepBack, 
  Play, 
  Pause, 
  StepForward, 
  SkipForward,
  RotateCcw,
  Download
} from 'lucide-react';

export function ReplayControls() {
  const {
    layers,
    layerCursor,
    setLayerCursor,
    simulationMode,
    setSimulationMode,
    replaySpeed,
    setReplaySpeed,
    isRunningSimulation,
  } = useSimulationStore();

  const handleStepBackward = () => {
    setLayerCursor(Math.max(0, layerCursor - 1));
  };

  const handleStepForward = () => {
    setLayerCursor(Math.min(layers.length - 1, layerCursor + 1));
  };

  const handleSkipToStart = () => {
    setLayerCursor(0);
  };

  const handleSkipToEnd = () => {
    setLayerCursor(layers.length - 1);
  };

  const handleToggleReplay = () => {
    if (simulationMode === 'REPLAY') {
      setSimulationMode('NORMAL');
    } else {
      setSimulationMode('REPLAY');
    }
  };

  const handleSpeedChange = (value: number[]) => {
    setReplaySpeed(value[0]);
  };

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          {/* Playback Controls */}
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleSkipToStart}
              disabled={layerCursor === 0}
            >
              <SkipBack className="h-4 w-4" />
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleStepBackward}
              disabled={layerCursor === 0}
            >
              <StepBack className="h-4 w-4" />
            </Button>
            
            <Button
              variant="outline"
              onClick={handleToggleReplay}
              className="px-4"
            >
              {simulationMode === 'REPLAY' && isRunningSimulation ? (
                <Pause className="h-4 w-4 mr-2" />
              ) : (
                <Play className="h-4 w-4 mr-2" />
              )}
              {simulationMode === 'REPLAY' ? 'Pause' : 'Replay'}
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleStepForward}
              disabled={layerCursor === layers.length - 1}
            >
              <StepForward className="h-4 w-4" />
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleSkipToEnd}
              disabled={layerCursor === layers.length - 1}
            >
              <SkipForward className="h-4 w-4" />
            </Button>
          </div>

          {/* Position Indicator */}
          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-600">
              Layer {layerCursor + 1} of {layers.length}
            </span>

            {/* Speed Control */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-600">Speed:</span>
              <div className="w-20">
                <Slider
                  value={[replaySpeed]}
                  onValueChange={handleSpeedChange}
                  min={0.1}
                  max={5}
                  step={0.1}
                  disabled={simulationMode !== 'REPLAY'}
                />
              </div>
              <span className="text-sm text-slate-600 w-8">
                {replaySpeed.toFixed(1)}x
              </span>
            </div>

            {/* Additional Controls */}
            <div className="flex gap-2">
              <Button variant="outline" size="sm">
                <RotateCcw className="h-4 w-4 mr-2" />
                Reset
              </Button>
              
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-4">
          <div className="w-full bg-slate-200 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ 
                width: `${layers.length > 0 ? ((layerCursor + 1) / layers.length) * 100 : 0}%` 
              }}
            />
          </div>
          <div className="flex justify-between text-xs text-slate-500 mt-1">
            <span>Start</span>
            <span>{simulationMode.toLowerCase()} mode</span>
            <span>End</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}