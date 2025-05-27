import React from 'react';
import { Progress } from '@/components/ui/progress';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { LayerState } from '@/types/simulation';
import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle } from 'lucide-react';

interface ConfidenceMeterProps {
  layers: LayerState[];
  showHistory?: boolean;
  showThresholds?: boolean;
}

export function ConfidenceMeter({ 
  layers, 
  showHistory = true, 
  showThresholds = true 
}: ConfidenceMeterProps) {
  
  const currentLayer = layers[layers.length - 1];
  const currentConfidence = currentLayer?.confidence?.score || 0;
  const currentDelta = currentLayer?.confidence?.delta || 0;
  const entropy = currentLayer?.confidence?.entropy || 0;

  // Calculate overall simulation confidence
  const overallConfidence = layers.length > 0 
    ? layers.reduce((acc, layer) => acc + layer.confidence.score, 0) / layers.length
    : 0;

  // Confidence thresholds
  const thresholds = {
    critical: 0.5,    // Below this triggers containment
    warning: 0.8,     // Below this shows warning
    good: 0.95,       // Above this is considered good
    excellent: 0.995  // Target threshold
  };

  const getConfidenceColor = (score: number) => {
    if (score >= thresholds.excellent) return 'text-green-600 bg-green-50';
    if (score >= thresholds.good) return 'text-green-500 bg-green-50';
    if (score >= thresholds.warning) return 'text-yellow-600 bg-yellow-50';
    if (score >= thresholds.critical) return 'text-orange-600 bg-orange-50';
    return 'text-red-600 bg-red-50';
  };

  const getConfidenceStatus = (score: number) => {
    if (score >= thresholds.excellent) return 'EXCELLENT';
    if (score >= thresholds.good) return 'GOOD';
    if (score >= thresholds.warning) return 'MODERATE';
    if (score >= thresholds.critical) return 'LOW';
    return 'CRITICAL';
  };

  const getProgressColor = (score: number) => {
    if (score >= thresholds.excellent) return 'bg-green-500';
    if (score >= thresholds.good) return 'bg-green-400';
    if (score >= thresholds.warning) return 'bg-yellow-500';
    if (score >= thresholds.critical) return 'bg-orange-500';
    return 'bg-red-500';
  };

  return (
    <div className="space-y-4">
      {/* Current Confidence */}
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium text-gray-700">Current Confidence</h3>
              <Badge className={cn('text-xs', getConfidenceColor(currentConfidence))}>
                {getConfidenceStatus(currentConfidence)}
              </Badge>
            </div>

            {/* Main confidence display */}
            <div className="text-center space-y-2">
              <div className="text-3xl font-bold flex items-center justify-center gap-2">
                <span className={cn(getConfidenceColor(currentConfidence).split(' ')[0])}>
                  {(currentConfidence * 100).toFixed(1)}%
                </span>
                {currentDelta !== 0 && (
                  <span className="flex items-center text-sm">
                    {currentDelta > 0 ? (
                      <TrendingUp className="w-4 h-4 text-green-500" />
                    ) : (
                      <TrendingDown className="w-4 h-4 text-red-500" />
                    )}
                    <span className={currentDelta > 0 ? 'text-green-500' : 'text-red-500'}>
                      {Math.abs(currentDelta * 100).toFixed(1)}%
                    </span>
                  </span>
                )}
              </div>

              {/* Progress bar */}
              <div className="relative">
                <Progress 
                  value={currentConfidence * 100} 
                  className="h-3"
                />
                <div 
                  className={cn('absolute top-0 left-0 h-3 rounded-full transition-all', getProgressColor(currentConfidence))}
                  style={{ width: `${currentConfidence * 100}%` }}
                />
              </div>
            </div>

            {/* Additional metrics */}
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Overall:</span>
                <div className="font-medium">
                  {(overallConfidence * 100).toFixed(1)}%
                </div>
              </div>
              <div>
                <span className="text-gray-500">Entropy:</span>
                <div className={cn(
                  'font-medium',
                  entropy > 0.1 ? 'text-red-600' : entropy > 0.05 ? 'text-yellow-600' : 'text-green-600'
                )}>
                  {(entropy * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Thresholds */}
      {showThresholds && (
        <Card>
          <CardContent className="pt-6">
            <h3 className="text-sm font-medium text-gray-700 mb-3">Confidence Thresholds</h3>
            <div className="space-y-2">
              {Object.entries(thresholds).reverse().map(([name, value]) => (
                <div key={name} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <div 
                      className={cn(
                        'w-3 h-3 rounded-full',
                        currentConfidence >= value ? 'bg-current' : 'bg-gray-300'
                      )}
                      style={{ 
                        color: currentConfidence >= value 
                          ? getProgressColor(value).replace('bg-', '') 
                          : undefined 
                      }}
                    />
                    <span className="capitalize">{name}</span>
                  </div>
                  <span className="font-mono">{(value * 100).toFixed(1)}%</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Confidence History */}
      {showHistory && layers.length > 0 && (
        <Card>
          <CardContent className="pt-6">
            <h3 className="text-sm font-medium text-gray-700 mb-3">Layer History</h3>
            <div className="space-y-2">
              {layers.map((layer, index) => (
                <div key={layer.layer} className="flex items-center gap-3 text-sm">
                  <Badge variant="outline" className="w-12 justify-center">
                    L{layer.layer}
                  </Badge>
                  
                  <div className="flex-1">
                    <Progress 
                      value={layer.confidence.score * 100} 
                      className="h-2"
                    />
                  </div>
                  
                  <div className="w-16 text-right font-mono">
                    {(layer.confidence.score * 100).toFixed(1)}%
                  </div>
                  
                  {layer.confidence.delta !== 0 && (
                    <div className={cn(
                      'w-12 text-xs text-right',
                      layer.confidence.delta > 0 ? 'text-green-500' : 'text-red-500'
                    )}>
                      {layer.confidence.delta > 0 ? '+' : ''}
                      {(layer.confidence.delta * 100).toFixed(1)}%
                    </div>
                  )}

                  {/* Status indicators */}
                  <div className="flex gap-1">
                    {layer.escalation && (
                      <AlertTriangle className="w-3 h-3 text-orange-500" />
                    )}
                    {layer.confidence.score >= thresholds.good && (
                      <CheckCircle className="w-3 h-3 text-green-500" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Safety Warnings */}
      {currentConfidence < thresholds.critical && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-red-700">
              <AlertTriangle className="w-5 h-5" />
              <div>
                <div className="font-medium">Critical Confidence Level</div>
                <div className="text-sm">
                  Confidence below {(thresholds.critical * 100)}% may trigger containment protocols
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
