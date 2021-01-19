# Kodestandard

## Introduksjon

Dette dokumentet definerer Team Dokumentløsninger sin kodestandard for apper teamet er ansvarlig for.

Dokumentet beskriver hvordan koden skal se ut, hvordan den skal struktureres og hvilke prinsipper for utvikling teamet skal forholde seg til.

## Kildekodefiler

### Tegnsett: UTF-8

Kildekodefiler skal være i UTF-8. Dette gjelder både filer med kompilerbar kode og konfigurasjonsfiler.

**Merknad:**

Applikasjonene under kan hende kjører som latin1 (ISO-8859-1) og det kan sette annet krav til tegnsett:

* joark
* ondemandbrev
* dialoguedlf
* brevserver

## Utviklingsprinsipper

* Endringer og feilrettinger brytes ned i oppgaver.
* Oppgaver representeres og dokumenteres ved saker i JIRA eller GitHub.
* Saker som utvikles skal estimeres av en utvikler med kjennskap til saken.

### Estimater

Formålet med estimater er å iverksette tiltak hvis man overskrider estimat. Estimatet sier noe om omfanget til oppgaven.
Hvis en oppgave estimeres til over maksimalt estimat, burde oppgaven brytes i flere deler.

Følgende estimater benyttes:

* XS - 4 timer (en halv arbeidsdag)
* S - 8 timer  (en arbeidsdag)
* M - 16 timer (to arbeidsdager)
* L -  40 timer (en arbeidsuke)
* XL - 60 timer (en og en halv arbeidsuke)


## Kodeprinsipper

For å sørge for at kode vi skriver er vedlikeholbart i lang tid fremover så er det hensiktsmessig å ha noen
prinsipper om hvordan vi skriver kode slik at det er enkelt å forstå og teste.
På toppniva kan dette summeres med KISS(https://en.wikipedia.org/wiki/KISS_principle) og
POLA(https://en.wikipedia.org/wiki/Principle_of_least_astonishment)

### Immutability og pure functions

Det er ofte hensiktsmessig å skrive kode hvor tilstand ikke endres og funksjoner heller returerer nye
immutable objekter. Det man får ut av dette er kode som er idempotent og som ikke skaper eller påvirkes av 
sideeffekter. Gevinsten med dette er at man kan lese og skjønne kode uten å måtte ta hensyn til konteksten
rundt, fn(x) vil alltid returnere det samme uavhengig av konteksten rundt. Dette gjør det også mye enklere å
teste kode da vi ikke lenger er nødt til å mocke resten av universet.

> You wanted a banana but what you got was a gorilla holding the banana and the entire jungle.
> -Joe Armstrong

```java
class Example {
    Pokemon levelUpPure(Pokemon pokemon) {
        return new Pokemon(pokemon.type, pokemon.level + 1);
    }

    void pureExample() {
        Pokemon purePokemon = new Pokemon("Pikachu", 10);
        Pokemon slightlyStrongerPurePokemon = levelUpPure(purePokemon);
        Pokemon anotherSlightlyStrongerPurePokemon = levelUpPure(purePokemon);
        // purePokemon: Pokemon {type: "Pikachu", level: 10}
        // slightlyStrongerPurePokemon: Pokemon {type: "Pikachu", level: 11}
        // anotherSlightlyStrongerPurePokemon: Pokemon {type: "Pikachu", level: 11}
    }

    void levelUpImpure(Pokemon pokemon) {
        pokemon.level = pokemon.level + 1;
    }
    
    void impureExample() {
        Pokemon impurePokemon = new Pokemon("Grimer", 10);
        levelUpImpure(impurePokemon);
        levelUpImpure(impurePokemon);
        // inpurePokemon: Pokemon {type: "Grimer", level: 12}
    }
}
```
I et leketøyeksempel som dette kan det virke uviktig,
men i en større kodebase blir du da nødt til å holde orden på når og hvor et objekt
blir mutert, samt hva du eventuelt påvirker når du muterer et objekt. Dette gjør det vanskligere 
å forstå kode, samtidig som det øker sjansen for å introdusere bugs og regresjoner.

### Annotasjoner

Annotasjoner er ment for å gjøre hverdagen til oss utviklere enklere. En stor del av nytteverdien i bruk av annotasjoner er å abstrahere bort boilerplate code slik at man som utviklere kan fokusere på det som utføres i koden. 

For eksempel vill lombok annotasjoner som *@Data* og *@Value* håndtere getters, setters, konstruktør etc, slik at man får lettleste klassser. Fokuset for neste utviklere som leser koden blir da på hvilke felter som finnes i klassen og på hvilke metoder i klassen som faktisk utfører domenerelavante processer.

Teamet vil at vi som utviklere skal hjelpe hverandre å skjønne intensjonen bak all kode vi skriver. Et tiltak vi har valgt for å støtte dette er å skrive ut felters spesifikasjoner eksplisitt. Med det mener vi for eksempel at vi skriver ut *"private final String navn"* til tross for at annotasjonen @Value generer spesifikasjonene for oss. 

Målet med koden er alltid at andre utviklere, og du selv om et halvår, skal kunne lese koden. 

## Testerprinsipper

Vi ønsker generelt en total testdekning på kode vi deployer til produksjon,
det vil si ett sett med unit tester for hver klasse (med unntak av rene dataklasser) og ett sett med integrasjonstester
for hver funksjonelle enhet (ex. tjoark203).
Generelt ønsker vi å plassere tester så lavt i testpyramiden som det praktisk lar seg gjøre.
Det vil si at det er ønskelig at vi primært bruker unit tester og kun bruke integrasjonstester der hvor det ikke praktisk er mulig å teste med unit tester.

## Navngivnig av tester
Navngivning av tester bør følge **ShouldWhen** konvensjonen slik at andre utviklere, og du selv om et halvår har nødvendig kontekst når det jobbes med koden.

```java
class TestNames{
    public void shouldFooWhenBar(){
    }

    public void shouldNotValidateAdresseWhenWhenAdresselinjeIsNull(){
    }
}
```