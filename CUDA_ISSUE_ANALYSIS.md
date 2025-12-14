# Анализ проблемы CUDA

## Проблема
```
CUDA error: operation not supported (cudaErrorNotSupported)
```

## Диагностика

### Обнаруженная конфигурация:
- **GPU:** NVIDIA GRID T4-16Q (Виртуализированная GPU)
- **Режим виртуализации:** VGPU (NVIDIA RTX Virtual Workstation)
- **Compute Capability:** 7.5 
- **PyTorch версия:** 2.9.1+cu128
- **CUDA версия драйвера:** 12.8
- **CUDA версия PyTorch:** 12.8
- **Доступная память GPU:** 17.18 GB

### Результаты тестирования:
✅ `torch.cuda.is_available()` = True
✅ `torch.cuda.device_count()` = 1  
✅ Compute Capability 7.5 поддерживается PyTorch
❌ `torch.zeros(1, device='cuda')` = **FAILED** с `cudaErrorNotSupported`

## Корневая причина

**Виртуализация GPU (vGPU) не полностью совместима с некоторыми CUDA операциями в PyTorch**

NVIDIA GRID/vGPU технология виртуализирует физическую GPU для использования в виртуальных машинах или контейнерах. Однако некоторые CUDA операции не поддерживаются или имеют ограничения в виртуализированной среде, особенно:
- Unified Memory операции
- Некоторые kernel launch конфигурации
- Определенные CUDA runtime API вызовы

## Решения

### ✅ Решение 1: Использовать CPU (РЕКОМЕНДУЕТСЯ - УЖЕ ПРИМЕНЕНО)

Ваш код уже имеет встроенный fallback механизм. Скрипт `run_app.sh` обновлен:

```bash
#!/bin/bash
source venv/bin/activate
export FORCE_CPU=1
streamlit run app.py
```

**Преимущества:**
- ✅ Стабильная работа без ошибок
- ✅ Не требует изменений кода
- ✅ Работает везде

**Недостатки:**
- ❌ Медленнее чем GPU (но для embedding моделей разница не критична)

### 🔧 Решение 2: Попробовать старую версию PyTorch

Некоторые старые версии PyTorch лучше работают с vGPU:

```bash
source venv/bin/activate
pip uninstall torch torchvision torchaudio -y
pip install torch==2.0.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**Риски:**
- Может потребовать переустановки sentence-transformers
- Не гарантирует решение проблемы

### 🔧 Решение 3: Использовать CUDA_LAUNCH_BLOCKING для отладки

```bash
export CUDA_LAUNCH_BLOCKING=1
export TORCH_USE_CUDA_DSA=1
```

Это поможет получить более детальную информацию об ошибках, но не исправит проблему.

### 🏢 Решение 4: Обратиться к администратору (долгосрочное)

Попросить:
1. Обновить NVIDIA vGPU драйверы
2. Проверить конфигурацию vGPU профиля
3. Рассмотреть возможность предоставления физической GPU или GPU passthrough

## Текущее состояние кода

Ваш код уже имеет защиту от CUDA ошибок:

### `src/utils.py`
```python
def get_compute_device():
    if torch.cuda.is_available():
        try:
            test_tensor = torch.zeros(1, device="cuda")
            del test_tensor
            torch.cuda.empty_cache()
            return "cuda"
        except Exception as e:
            print(f"CUDA is available but not working properly: {e}")
            print("Falling back to CPU")
            return "cpu"
```

### `src/embeddings.py`
```python
try:
    self.model = SentenceTransformer(EMBEDDING_MODEL_NAME, device=device)
except Exception as e:
    if device == "cuda":
        print(f"Failed to load model on CUDA: {e}")
        print("Retrying with CPU...")
        device = "cpu"
        self.model = SentenceTransformer(EMBEDDING_MODEL_NAME, device=device)
```

### `src/agent.py`
```python
try:
    self.reranker = CrossEncoder('BAAI/bge-reranker-v2-m3', device=device)
except Exception as e:
    if device == "cuda":
        print(f"Failed to load Re-ranker on CUDA: {e}")
        print("Retrying with CPU...")
        device = "cpu"
        self.reranker = CrossEncoder('BAAI/bge-reranker-v2-m3', device=device)
```

## Рекомендация

**Используйте CPU режим через `FORCE_CPU=1`**

Причины:
1. ✅ Стабильная работа гарантирована
2. ✅ Для embedding моделей среднего размера CPU вполне приемлем
3. ✅ Избежание случайных CUDA ошибок в продакшене
4. ✅ Ваш код уже оптимизирован для этого

Если производительность CPU недостаточна, рассмотрите:
- Использование более легких embedding моделей
- Кэширование embeddings
- Батчинг запросов

## Проверка производительности

Запустите бенчмарк:
```bash
source venv/bin/activate
export FORCE_CPU=1
python check_hardware.py
```

Это покажет реальную скорость обработки на CPU.
