import React, { useState } from 'react';

function Dashboard() {
  const [hasStarted, setHasStarted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [schedule, setSchedule] = useState([]);
  const [inventoryStatus, setInventoryStatus] = useState({});

  const [formData, setFormData] = useState({
    vehicle_type: '',
    engine: '',
    paint: '',
    airbag: '',
    sensor_basic: '',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const isFormValid = Object.values(formData).every((val) => val !== '');

  const handleStart = async () => {
    setHasStarted(true);
    setLoading(true);
    try {
      await fetch('http://localhost:8000/process_data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ csv_path: 'backend\\data\\datasets\\market_demand.csv' }),
      });

      const featuresList = [
        `engine_${formData.engine}`,
        `tire_allseason`,
        `paint_${formData.paint}`,
        `airbag_${formData.airbag}`,
      ];

      if (formData.sensor_basic === 'yes') {
        featuresList.push('sensor_basic');
      }

      const features = featuresList.join(',');


      const inventoryRes = await fetch('http://localhost:8000/check_inventory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config: { features } }),
      });
      const inventoryData = await inventoryRes.json();
      setInventoryStatus(inventoryData || {});

      
      const scheduleRes = await fetch('http://localhost:8000/schedule', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            vehicle_type: formData.vehicle_type,
            features: featuresList, // or features if you want it as a string
}),
      });

      const scheduleData = await scheduleRes.json();
      setSchedule(scheduleData.schedule || []);
    } catch (error) {
      console.error('Fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!hasStarted) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 px-4">
        <h1 className="text-4xl font-bold text-blue-700 mb-2">Smart Production Scheduler</h1>
        <p className="text-gray-600 mb-8 text-center max-w-xl">
          Optimize your vehicle production line based on market demand and inventory availability.
        </p>

        <div className="bg-white p-6 rounded-lg shadow-md w-full max-w-2xl">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Vehicle Type</label>
              <select name="vehicle_type" value={formData.vehicle_type} onChange={handleChange} className="mt-1 block w-full border rounded px-3 py-2 text-sm">
                <option value="">-- Select --</option>
                <option value="Sedan">Sedan</option>
                <option value="SUV">SUV</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Engine</label>
              <select name="engine" value={formData.engine} onChange={handleChange} className="mt-1 block w-full border rounded px-3 py-2 text-sm">
                <option value="">-- Select --</option>
                <option value="normal">Normal</option>
                <option value="hybrid">Hybrid</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Paint</label>
              <select name="paint" value={formData.paint} onChange={handleChange} className="mt-1 block w-full border rounded px-3 py-2 text-sm">
                <option value="">-- Select --</option>
                <option value="red">Red</option>
                <option value="blue">Blue</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Airbag</label>
              <select name="airbag" value={formData.airbag} onChange={handleChange} className="mt-1 block w-full border rounded px-3 py-2 text-sm">
                <option value="">-- Select --</option>
                <option value="standard">Standard</option>
                <option value="premium">Premium</option>
              </select>
            </div>
          </div>

          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">Sensor Basic</label>
            <div className="flex gap-6">
              <label className="inline-flex items-center">
                <input type="radio" name="sensor_basic" value="yes" checked={formData.sensor_basic === 'yes'} onChange={handleChange} className="form-radio" />
                <span className="ml-2 text-sm">Yes</span>
              </label>
              <label className="inline-flex items-center">
                <input type="radio" name="sensor_basic" value="no" checked={formData.sensor_basic === 'no'} onChange={handleChange} className="form-radio" />
                <span className="ml-2 text-sm">No</span>
              </label>
            </div>
          </div>

          <div className="mt-6 flex justify-center">
            <button
              onClick={handleStart}
              disabled={!isFormValid}
              className={`px-6 py-2 rounded text-white text-sm font-medium transition ${
                isFormValid ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-300 cursor-not-allowed'
              }`}
            >
              Start Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-gray-100">
        <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-blue-500 border-solid mb-4"></div>
        <div className="text-lg font-semibold text-gray-700">Loading data...</div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <h1 className="text-3xl font-bold mb-6 text-center text-blue-700">
        Production Scheduling Dashboard
      </h1>
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        <div className="bg-white border p-6 rounded-lg shadow md:col-span-4">
          <h2 className="text-xl font-semibold mb-2 text-gray-800">Inventory Status</h2>
          {Object.keys(inventoryStatus).length === 0 ? (
            <p className="text-gray-500">No inventory data available.</p>
          ) : (
            <table className="min-w-full text-sm text-left text-gray-700">
              <thead className="bg-gray-100 text-xs uppercase text-gray-500">
                <tr>
                  <th className="px-4 py-2">Feature</th>
                  <th className="px-4 py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(inventoryStatus).map(([key, value]) => (
                  <tr key={key} className="border-t">
                    <td className="px-4 py-2">{key}</td>
                    <td className="px-4 py-2">
                      {typeof value === 'object' && value !== null ? (
                        <ul className="list-disc list-inside">
                          {Object.entries(value).map(([k, v]) => (
                            <li key={k}>{k}: {v}</li>
                          ))}
                        </ul>
                      ) : (
                        String(value)
                      )}
                    </td>

                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="bg-white border p-6 rounded-lg shadow md:col-span-8">
          <h2 className="text-xl font-semibold mb-2 text-gray-800">Production Schedule</h2>
          <table className="min-w-full text-sm text-left text-gray-700">
            <thead className="bg-gray-100 text-xs uppercase text-gray-500">
              <tr>
                <th className="px-4 py-2">Day</th>
                <th className="px-4 py-2">Vehicle Type</th>
                <th className="px-4 py-2">Features</th>
                <th className="px-4 py-2">Quantity</th>
              </tr>
            </thead>
            <tbody>
              {schedule.map((item, index) => (
                <tr key={index} className="border-t">
                  <td className="px-4 py-2">{item.day}</td>
                  <td className="px-4 py-2">{item.vehicle_type}</td>
                  <td className="px-4 py-2">{item.features}</td>
                  <td className="px-4 py-2">{item.quantity}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
