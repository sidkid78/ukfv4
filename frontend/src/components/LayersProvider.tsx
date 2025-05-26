import React, { createContext, useContext, useState, ReactNode } from 'react';

export type Layer = {
  id: number;
  name: string;
  visible: boolean;
  // Add more properties as needed
};

interface LayersContextProps {
  layers: Layer[];
  setLayerVisible: (id: number, visible: boolean) => void;
}

const LayersContext = createContext<LayersContextProps | undefined>(undefined);

export const LayersProvider = ({ children }: { children: ReactNode }) => {
  const [layers, setLayers] = useState<Layer[]>(
    Array.from({ length: 10 }, (_, i) => ({ id: i + 1, name: `Layer ${i + 1}`, visible: true }))
  );

  const setLayerVisible = (id: number, visible: boolean) => {
    setLayers(prev => prev.map(l => l.id === id ? { ...l, visible } : l));
  };

  return (
    <LayersContext.Provider value={{ layers, setLayerVisible }}>
      {children}
    </LayersContext.Provider>
  );
};

export const useLayers = () => {
  const ctx = useContext(LayersContext);
  if (!ctx) throw new Error('useLayers must be used within a LayersProvider');
  return ctx;
};
