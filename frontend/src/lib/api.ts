// ------------------------------------------------------------------------
// 2. API Library Function (e.g., in src/lib/api.ts)
// ------------------------------------------------------------------------
// Make sure to set NEXT_PUBLIC_API_BASE_URL in your .env.local file

import { AxisMetadata } from "@/types/axis";

// e.g., NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchAxesMetadata(): Promise<AxisMetadata[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/axis/`);
    if (!response.ok) {
      // Log the error status and text for more detailed debugging
      const errorText = await response.text();
      console.error(`API Error: ${response.status} - ${errorText}`);
      throw new Error(`Failed to fetch axes metadata. Status: ${response.status}`);
    }
    const data: AxisMetadata[] = await response.json();
    return data;
  } catch (error) {
    console.error("Error fetching axes metadata:", error);
    // Re-throw the error so it can be caught by the component
    throw error; 
  }
}
