# Universiteto duomenų bazės API

## Aprašymas

Šis API duoda prieiga prie duomenų bazės ir duoda taškus per kuriuos galima pridėti, panaikinti bei peržiurėti duomenis. Šis API jungiasi prie MongoDB duomenų bazės.

---

## Pagrindinis URL
`http://localhost:5000`

---

## Kaip ši duomenų bazė gali būti išplėsta dideliam kiekiui vartotojų
- Šiuo metu duomenų bazėje jau naudojama duomenų replikacija tam kad daugelis vartotojų neapkrautų vieno taško, ir tam kad jie galėtų gauti duomenis greičiau  priklausant nuo jų lokacijos.
- Duomenų bazė taip pat paruošta skaidymui, galime panaudoti skaidyma ant studentų grupių arba studentų specialybių tam kad atitinkamam fakultetui būtų greitai bei patogiai pasiekiami jų duomenys.
- Indeksavimas - ši duomenų bazė turi indeksus ant studentų įstojimo metų, studentų id, grupės turi indeksus pagal specialybės bei savo id, specialybės turi indeksus pagal savo id, bei pavadinima, santykiai turi indeksus pagal santykinio elemento id (grupės arba dėstomo dalyko) bei ant santykio rūšies, galiausiai dėstomi dalykai turi indeksus ant pavadinimo ir id.


## Galutiniai taškai

### Studentai

#### Pridėti studenta
- **URL:** `/students`
- **Metodas:** `PUT`
- **Aprašymas:** Prideda nauja studenta prie duomenu bazes
- **Užklausos duomenys:**
  ```json
  {
    "name": "John",
    "surname": "Doe",
    "date_of_birth": "2000-01-01",
    "join_year": 2023
  }
  ```
- **Galimi atsakymai**:
    ```
    Success (201): { "id": "S2300001" }
    ```
    ```
    Error (400): "Not enough information"
    ```

#### Gražink studenta

- **URL:** `/students/<students_id>`
- **Metodas:** `GET`
- **Aprašymas:** Gražina studenta iš duomenų bazės
- **Galimi atsakymai**:
  ```
  Success (200):
    {
    "id": "S2300001",
    "name": "John",
    "surname": "Doe",
    "date_of_birth": "2000-01-01",
    "join_date": "2023-09-01"
    }
  ```
  ```
  Error (404): "not found"
  ```

### Specialybės
#### Pridėk specialybę
- **URL:** `/specialties`
- **Metodas:** `PUT`
- **Aprašymas:** Prideda nauja specialybę prie duomenų bazės
- **Užklausos duomenys**:
```json
    {
      "name": "Computer Science"
    }
```

- **Galimi atsakymai**:
    ```
    Success (200): { "id": "SP00000001" }
    ```
    ```
    Error (400): "Not enough information"
    ```

#### Gražink visas specialybes

- **URL:** `/specialties`
- **Metodas:** `GET`
- **Aprašymas:** Gražina visas specialybes iš duomenų bazės
- **Galimi atsakymai**:
    ```json
    [
      {
        "id": "SP00000001",
        "name": "Computer Science"
      }
    ]
    ```

#### Gražink studentus pagal specialybes
- **URL:** `/specialties/<specialty_id>/students`
- **Metodas:** `GET`
- **Aprašymas:** Gražina visus studentus studijuojančius specialybėje iš duomenų bazės
- **Galimi atsakymai**:
  ```json
  [
    {
      "id": "S2300001",
      "name": "John",
      "surname": "Doe",
      "date_of_birth": "2000-01-01",
      "join_date": "2023-09-01"
    }, 
    {"...": "..."}
  ]
  ```
  ```
  Error (404) "Data not found"
  ```
### Grupės
#### Pridėk grupe
- **URL:** `/specialties/<specialty_id>/groups`
- **Metodas:** `PUT`
- **Aprašymas:** Prideda grupe prie duomenų bazės
- **Galimi atsakymai**:
  ```
  Success (201): { "id": "CS001" }
  ```

### Visos specialybės grupės
- **URL:** `/specialties/<specialty_id>/groups`
- **Metodas:** `GET`
- **Aprašymas:** Gražina visas specialybės grupes
- **Galimi atsakymai**:
  ```json
  [
    {
      "id": "CS001",
      "specialty_id": "SP00000001"
    }
  ]
  ```
    ```
  Error (404) "Data not found"
  ```
### Dėstomi dalykai
### Pridėk dėstoma dalyka
- **URL:** `/subjects`
- **Metodas:** `PUT`
- **Aprašymas:** Prideda nauja dėstoma dalyka prie duomenų bazės
- **Užklausos duomenys:**
  ```json
  {
    "title": "Algorithms",
    "lecturer_name": "Jane",
    "lecturer_surname": "Smith",
    "semester": 1
  }
  ```

- **Galimi atsakymai:**
  ```
  Success (201): { "id": "SB00000001" }
  Error (400): "Not enough information"
  ```
#### Gražink visus dėstomus dalykus
- **URL:** `/subjects`
- **Metodas:** `GET`
- **Aprašymas:** Gražina visas specialybės grupes
- **Galimi atsakymai**:
  ```json
  [
    {
      "id": "SB00000001",
      "title": "Algorithms",
      "lecturer_name": "Jane",
      "lecturer_surname": "Smith",
      "semester": 1
    }
  ]
  ```
    ```
  Error (404) "Data not found"
  ```
### Santykiai
#### Pridėk studenta prie grupės
- **URL:** `/groups/<group_id>/students/<student_id>`
- **Metodas:** `PUT`
- **Aprašymas:** Prideda studenta prie grupės (Šiam grupės adresavimui parinktas kitoks adresas, nei prieš tai nes grupė čia matoma kaip atskiras dalykas nuo specialybės)
- **Galimi atsakymai**:
  ```
  Success (201): "Student added to group"
  Error (404): "Student not found" arba "Group not found"
  ```
#### Pridėk studenta prie dėstomo dalyko
- **URL:** `/subjects/<subject_id>/students/<student_id>`
- **Metodas:** `PUT`
- **Aprašymas:** Prideda studenta prie dėstomo dalyko
- **Galimi atsakymai**:
  ```
  Success (201): "Student added to subject"
  Error (404): "Student not found" arba "Subject not found"
  ```
### Gauk visus grupės arba dėstomo dalyko studentus
- **URL:** `/groups/<relation_id>/students` arba `/subjects/<relation_id>/students`
- **Metodas:** `GET`
- **Aprašymas:** Gauk visus grupės arba dėstomo dalyko studentus
- **Galimi atsakymai**:
  ```json
  [
    {
      "id": "S2300001",
      "name": "John",
      "surname": "Doe",
      "date_of_birth": "2000-01-01",
      "join_date": "2023-09-01"
    }
  ]
  ```
    ```
  Error (404) "Data not found"
  ```
### Pagalbinės priemonės
#### Duomenų bazės išvalymas
- **URL:** `/cleanup`
- **Metodas:** `PUT`
- **Aprašymas:** Ištrina visus duomenu bazės duomenis palikdamas tik laikmenas.
- **Galimi atsakymai**:
  ```
  Success (200): "database cleaned"
  ```