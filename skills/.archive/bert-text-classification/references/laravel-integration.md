# Laravel Integration for BERT Text Classification

Integrate a Python FastAPI BERT-classification microservice with Laravel.

## Architecture

```
Laravel app → HTTP POST → Python FastAPI (:8000) → BERT model → JSON response
```

The Python service runs as a **Supervisor-managed daemon** on the same machine (or internal network). Laravel calls it via `Illuminate\Support\Facades\Http`.

## Files to add to your Laravel project

### 1. Controller

```php
<?php
// app/Http/Controllers/Api/EpostKlassifiseringController.php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class EpostKlassifiseringController extends Controller
{
    protected string $serviceUrl;
    protected string $apiKey;

    public function __construct()
    {
        $this->serviceUrl = config('services.epostklassifisering.url', 'http://127.0.0.1:8000');
        $this->apiKey = config('services.epostklassifisering.api_key');
    }

    public function klassifiser(Request $request)
    {
        $validated = $request->validate([
            'tekst' => 'required|string|min:1|max:5000',
        ]);

        try {
            $response = Http::timeout(10)
                ->withHeaders($this->getHeaders())
                ->post("{$this->serviceUrl}/klassifiser", $validated);

            if ($response->failed()) {
                Log::error('Klassifisering feilet', ['status' => $response->status()]);
                return response()->json(['label' => 'ukjent'], 200);
            }

            return response()->json($response->json());
        } catch (\Throwable $e) {
            Log::error('Klassifisering unntak: ' . $e->getMessage());
            return response()->json(['label' => 'ukjent'], 200);
        }
    }

    public function health()
    {
        try {
            $response = Http::timeout(5)->get("{$this->serviceUrl}/health");
            return response()->json($response->json());
        } catch (\Throwable $e) {
            return response()->json(['status' => 'unavailable'], 503);
        }
    }

    protected function getHeaders(): array
    {
        $headers = ['Content-Type' => 'application/json'];
        if ($this->apiKey) {
            $headers['X-API-Key'] = $this->apiKey;
        }
        return $headers;
    }
}
```

### 2. Routes

```php
// routes/api.php
Route::prefix('epost')->group(function () {
    Route::post('/klassifiser', [EpostKlassifiseringController::class, 'klassifiser']);
    Route::get('/health', [EpostKlassifiseringController::class, 'health']);
});
```

### 3. Config

```php
// config/services.php
'epostklassifisering' => [
    'url' => env('EPOSTKLASSIFISERING_URL', 'http://127.0.0.1:8000'),
    'api_key' => env('EPOSTKLASSIFISERING_API_KEY'),
],
```

### 4. .env

```
EPOSTKLASSIFISERING_URL=http://127.0.0.1:8000
EPOSTKLASSIFISERING_API_KEY=
```

## Design decisions

- **Fallback to 'ukjent':** If the Python service is down, return 200 with `"label": "ukjent"`. The email queue should never crash because the ML model is unavailable.
- **10-second timeout:** If the model is cold-starting or busy, don't let it hang the HTTP request.
- **Internal port 8000:** Bind the Python service to `127.0.0.1:8000` only — never expose it to the public internet. Laravel's API endpoints are the public face.

## Scaling

For high throughput (>100 req/s):
1. Add a queue job: Laravel dispatches a job, a worker calls the Python service
2. Multiple uvicorn workers: `uvicorn serve:app --workers 4`
3. Separate the microservice onto its own server with a load balancer
